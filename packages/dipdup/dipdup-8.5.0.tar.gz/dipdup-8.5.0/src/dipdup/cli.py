# NOTE: All imports except the basic ones are very lazy in this module. Let's keep it that way.
import asyncio
import logging
import sys
from collections.abc import Callable
from collections.abc import Coroutine
from contextlib import AsyncExitStack
from contextlib import suppress
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import TypeVar
from typing import cast

import click
import uvloop

from dipdup import env
from dipdup.install import EPILOG
from dipdup.install import WELCOME_ASCII

if TYPE_CHECKING:
    from dipdup.config import DipDupConfig

CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
    'max_content_width': 120,
}

# NOTE: Do not try to load config for these commands as they don't need it
NO_CONFIG_CMDS = {
    'new',
    'migrate',
    'config',  # this one too
}

# NOTE: Click commands from `aerich` we use as is for database migration
AERICH_CMDS = {
    'history',
    'heads',
    'migrate',
    'upgrade',
    'downgrade',
}
ALWAYS_IMMUNE_TABLES = {'dipdup_meta', 'aerich'}

_logger = logging.getLogger(__name__)
_click_wrap_text = click.formatting.wrap_text


def _wrap_text(text: str, *a: Any, **kw: Any) -> str:
    # NOTE: WELCOME_ASCII and EPILOG
    if text.startswith('    '):
        return text
    if text.startswith('\0\n'):
        return text[2:]
    return _click_wrap_text(text, *a, **kw)


click.formatting.wrap_text = _wrap_text


def _get_paths(
    params: dict[str, Any],
) -> tuple[list[Path], list[Path]]:
    from dipdup.exceptions import ConfigurationError
    from dipdup.package import ROOT_CONFIG

    config_args: list[str] = params.pop('config', [])
    env_file_args: list[str] = params.pop('env_file', [])
    config_alias_args: list[str] = params.pop('c', [])

    config_paths: list[Path] = []
    env_file_paths: list[Path] = []

    if config_alias_args:
        if config_args:
            raise ConfigurationError('Cannot use both `-c` and `-C` options at the same time')
        config_args = [
            ROOT_CONFIG,
            *[f'configs/dipdup.{name}.yaml' for name in config_alias_args],
        ]
    config_args = config_args or [ROOT_CONFIG]

    for arg in config_args:
        path = Path(arg)
        if path.is_dir():
            path = path / ROOT_CONFIG
        if not path.is_file():
            raise ConfigurationError(f'Config file not found: {path}')
        config_paths.append(path)

    for arg in env_file_args:
        path = Path(arg)
        if not path.is_file():
            raise ConfigurationError(f'Env file not found: {path}')
        env_file_paths.append(path)

    return config_paths, env_file_paths


def _load_env_files(env_file_paths: list[Path]) -> None:
    from dipdup.package import CWD_ENV

    # NOTE: If 'dipdup.env' exists it's loaded automatically after other files
    if (cwd_env := Path.cwd().joinpath(CWD_ENV)).is_file():
        env_file_paths.append(cwd_env)

    for path in env_file_paths:
        from dotenv import load_dotenv

        _logger.info('Applying env_file `%s`', path)
        load_dotenv(path, override=True)

    # NOTE: Make `dipdup.env` aware of possible changes
    if env_file_paths:
        env.reload_env()


def echo(message: str, err: bool = False, **styles: Any) -> None:
    with suppress(BrokenPipeError):
        click.secho(message, err=err, **styles)


def big_yellow_echo(message: str) -> None:
    echo(f'\n{message}\n', fg='yellow')


def green_echo(message: str) -> None:
    echo(message, fg='green')


def red_echo(message: str) -> None:
    echo(message, err=True, fg='red')


def _print_help_atexit(error: Exception, report_id: str) -> None:
    """Prints a helpful error message after the traceback"""
    import atexit
    import traceback

    from dipdup.exceptions import CallbackError
    from dipdup.exceptions import Error

    def _print() -> None:
        nonlocal error

        if isinstance(error, Error):
            echo(error.help(), err=True)
        else:
            # NOTE: Check the traceback to find out if exception is from a callback
            tb = traceback.extract_tb(error.__traceback__)
            for frame in tb:
                if frame.name == 'fire_handler':
                    modules = tuple(f.filename for f in tb if '/handlers/' in f.filename or '/hooks/' in f.filename)
                    module = '.'.join(Path(f).stem for f in modules)
                    echo(CallbackError(module=module, exc=error).help(), err=True)
                    break
            else:
                echo(Error.default_help(), err=True)

        echo(f'Report saved; run `dipdup report show {report_id}` to view it', err=True)

    atexit.register(_print)


WrappedCommandT = TypeVar('WrappedCommandT', bound=Callable[..., Coroutine[Any, Any, None]])


@dataclass
class CLIContext:
    config_paths: list[str]
    config: 'DipDupConfig'

    # NOTE: We need this because aerich Click commands expect `ctx.obj` object to be a dict.
    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)


def _cli_wrapper(fn: WrappedCommandT) -> WrappedCommandT:
    @wraps(fn)
    def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> None:
        try:
            uvloop.run(fn(ctx, *args, **kwargs))
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        except Exception as e:
            if isinstance(e, click.UsageError):
                raise

            from dipdup.report import save_report

            package = ctx.obj.config.package if ctx.obj else 'unknown'
            report_id = save_report(package, e)
            _print_help_atexit(e, report_id)
            raise e

        # NOTE: If indexing was interrupted by signal, save report with just performance metrics.
        if fn.__name__ == 'run' and not env.TEST:
            from dipdup.report import save_report

            package = ctx.obj.config.package
            save_report(package, None)

    return cast('WrappedCommandT', wrapper)


def _cli_unwrapper(cmd: click.Command) -> Callable[..., Coroutine[Any, Any, None]]:
    return cmd.callback.__wrapped__.__wrapped__  # type: ignore[no-any-return,union-attr]


def _skip_cli_group() -> bool:
    # NOTE: Workaround for help pages. First argument check is for the test runner.
    args = sys.argv[1:]
    is_help = '--help' in args or '-h' in args
    is_empty_group = args[-1:] in (
        ['config'],
        ['hasura'],
        ['mcp'],
        ['package'],
        ['schema'],
    )
    # NOTE: Simple helpers that don't use any of our cli boilerplate
    is_script_group = args[0] in (
        'report',
        'self',
    )

    if is_help or is_empty_group or is_script_group:
        return True
    return False


@click.group(
    context_settings=CONTEXT_SETTINGS,
    help=WELCOME_ASCII,
    epilog=EPILOG,
)
@click.version_option()
@click.option(
    '--config',
    '-c',
    type=str,
    multiple=True,
    help='A path to DipDup project config.',
    default=[],
    metavar='PATH',
    envvar='DIPDUP_CONFIG',
)
@click.option(
    '--env-file',
    '-e',
    type=str,
    multiple=True,
    help='A path to .env file containing `KEY=value` strings.',
    default=[],
    metavar='PATH',
    envvar='DIPDUP_ENV_FILE',
)
@click.option(
    '-C',
    type=str,
    multiple=True,
    help='A shorthand for `-c . -c configs/dipdup.<name>.yaml`',
    default=[],
    metavar='NAME',
)
@click.pass_context
@_cli_wrapper
async def cli(ctx: click.Context, config: list[str], env_file: list[str], c: list[str]) -> None:
    from dipdup.sys import set_up_process

    set_up_process()

    # FIXME: This check fails for non-existing commands. Some Click magic could help here.
    if _skip_cli_group():
        return

    # NOTE: https://github.com/python/cpython/issues/95778
    # NOTE: Method is not available in early Python 3.12
    try:
        sys.set_int_max_str_digits(0)
    except AttributeError:
        _logger.warning("You're running an outdated Python 3.12 release; consider upgrading")

    from dipdup.sys import set_up_logging

    set_up_logging()

    # NOTE: These commands need no other preparations
    if ctx.invoked_subcommand in NO_CONFIG_CMDS:
        logging.getLogger('dipdup').setLevel(logging.INFO)
        return

    from dipdup.config import DipDupConfig
    from dipdup.exceptions import InitializationRequiredError
    from dipdup.package import DipDupPackage

    # NOTE: Early config loading; some commands do it later
    config_paths, env_file_paths = _get_paths(ctx.params)
    # NOTE: Apply env files before loading the config
    _load_env_files(env_file_paths)

    _config = DipDupConfig.load(
        paths=config_paths,
        environment=True,
        raw=False,
        unsafe=True,
    )
    _config.set_up_logging()

    if _config.sentry:
        from dipdup.sentry import init_sentry

        init_sentry(_config.sentry, _config.package)

    # NOTE: Imports will be loaded later if needed
    _config.initialize()

    # NOTE: Fire and forget, do not block instant commands
    if not (env.TEST or env.is_in_gha() or env.NO_VERSION_CHECK):
        from dipdup._version import check_version

        # FIXME: https://github.com/dipdup-io/dipdup/issues/1114; replace with `fire_and_forget` call once resolved.
        await check_version()

    try:
        # NOTE: Avoid early import errors if project package is incomplete.
        # NOTE: `ConfigurationError` will be raised later with more details.
        DipDupPackage(_config.package_path, quiet=True).initialize()
    except Exception as e:
        if ctx.invoked_subcommand != 'init':
            raise InitializationRequiredError(f'Failed to create a project package: {e}') from e

    ctx.obj = CLIContext(
        config_paths=config,
        config=_config,
    )


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def run(ctx: click.Context) -> None:
    """Run the indexer.

    Execution can be gracefully interrupted with `Ctrl+C` or `SIGINT` signal.
    """
    from dipdup.dipdup import DipDup

    config: DipDupConfig = ctx.obj.config
    config.initialize()

    dipdup = DipDup(config)
    await dipdup.run()


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option('--force', '-f', is_flag=True, help='Overwrite existing types and ABIs.')
@click.option('--base', '-b', is_flag=True, help='Include template base (default)')
@click.option('--no-base', is_flag=True, help='Skip files from base template.')
@click.option('--no-linter', is_flag=True, help='Skip applying linter and formatter.')
@click.option('--no-types', is_flag=True, help='Skip generating ABIs and typeclasses.')
@click.argument(
    'include',
    type=str,
    nargs=-1,
    metavar='PATH',
)
@click.pass_context
@_cli_wrapper
async def init(
    ctx: click.Context,
    force: bool,
    base: bool,
    no_base: bool,
    no_linter: bool,
    no_types: bool,
    include: list[str],
) -> None:
    """Generate project tree, typeclasses and callback stubs.

    This command is idempotent, meaning it won't overwrite previously generated files unless asked explicitly.
    """
    from dipdup.dipdup import DipDup

    if base:
        if no_base:
            raise click.BadParameter('You cannot use both `--base` and `--no-base` options at the same time')
        _logger.warning('`--base` option became default; use `--no-base` to disable it')

    config: DipDupConfig = ctx.obj.config
    dipdup = DipDup(config)

    await dipdup.init(
        force=force,
        no_base=no_base,
        no_linter=no_linter,
        no_types=no_types,
        include=set(include),
    )


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option('--dry-run', '-n', is_flag=True, help='Print changes without applying them.')
@click.pass_context
@_cli_wrapper
async def migrate(ctx: click.Context, dry_run: bool) -> None:
    """
    Migrate project to the new spec version.

    If you're getting `MigrationRequiredError` after updating DipDup, this command will fix imports and type annotations to match the current `spec_version`. Review and commit changes after running it.
    """
    from dipdup.config import DipDupConfig
    from dipdup.migrations.three_zero import ThreeZeroProjectMigration

    # NOTE: Late loading: can't load config with old spec version
    assert ctx.parent
    config_paths, env_file_paths = _get_paths(ctx.parent.params)
    _load_env_files(env_file_paths)

    migration = ThreeZeroProjectMigration(tuple(config_paths), dry_run)
    migration.migrate()

    config = DipDupConfig.load(
        paths=config_paths,
        environment=True,
        raw=False,
        unsafe=True,
    )
    config.initialize()

    ctx.obj = CLIContext(
        config_paths=ctx.parent.params['config'],
        config=config,
    )
    await _cli_unwrapper(init)(
        ctx=ctx,
        base=False,
        force=True,
        no_linter=True,
        no_base=False,
        no_types=False,
        include=[],
    )


@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def config(ctx: click.Context) -> None:
    """Commands to manage DipDup configuration."""
    pass


@config.command(name='export', context_settings=CONTEXT_SETTINGS)
@click.option('--unsafe', is_flag=True, help='Use actual environment variables instead of default values.')
@click.option('--full', '-f', is_flag=True, help='Resolve index templates.')
@click.option('--raw', '-r', is_flag=True, help='Do not initialize config; preserve file structure.')
@click.pass_context
@_cli_wrapper
async def config_export(
    ctx: click.Context,
    unsafe: bool,
    full: bool,
    raw: bool,
) -> None:
    """
    Print config after resolving all links and, optionally, templates.

    WARNING: Avoid sharing output with 3rd-parties when `--unsafe` flag set - it may contain secrets!
    """
    from dipdup.config import DipDupConfig
    from dipdup.yaml import DipDupYAMLConfig

    # NOTE: Late loading; cli() was skipped.
    config_paths, env_file_paths = _get_paths(ctx.parent.parent.params)  # type: ignore[union-attr]
    _load_env_files(env_file_paths)

    if raw:
        raw_config, _ = DipDupYAMLConfig.load(
            paths=config_paths,
            environment=False,
            raw=True,
            unsafe=unsafe,
        )
        echo(raw_config.dump())

    else:
        config = DipDupConfig.load(
            paths=config_paths,
            environment=True,
            raw=False,
            unsafe=unsafe,
        )
        if full:
            config.initialize()
        echo(config.dump())


@config.command(name='env', context_settings=CONTEXT_SETTINGS)
@click.option('--output', '-o', type=str, default=None, help='Output to file instead of stdout.')
@click.option('--unsafe', is_flag=True, help='Use actual environment variables instead of default values.')
@click.option('--compose', '-c', is_flag=True, help='Output in docker-compose format.')
@click.option('--internal', '-i', is_flag=True, help='Include internal variables.')
@click.pass_context
@_cli_wrapper
async def config_env(
    ctx: click.Context,
    output: str | None,
    unsafe: bool,
    compose: bool,
    internal: bool,
) -> None:
    """Dump environment variables used in DipDup config.

    If variable is not set, default value will be used.
    """
    from dipdup.yaml import DipDupYAMLConfig

    # NOTE: Late loading; cli() was skipped.
    config_paths, env_file_paths = _get_paths(ctx.parent.parent.params)  # type: ignore[union-attr]
    _load_env_files(env_file_paths)

    _, environment = DipDupYAMLConfig.load(
        paths=config_paths,
        environment=True,
        raw=False,
        unsafe=unsafe,
    )
    if internal:
        environment.update(env.dump())
    if compose:
        content = 'services:\n  dipdup:\n    environment:\n'
        _tab = ' ' * 6
        for k, v in sorted(environment.items()):
            line = f'{_tab}- {k}=' + '${' + k
            if v is not None:
                line += ':-' + v + '}'
            else:
                line += '}'

            content += line + '\n'
    else:
        content = '\n'.join(f'{k}={v}' for k, v in sorted(environment.items()))
    if output:
        Path(output).write_text(content)
    else:
        echo(content)


@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def hasura(ctx: click.Context) -> None:
    "Commands related to Hasura integration."

    pass


@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def mcp(ctx: click.Context) -> None:
    "Commands related to MCP integration."
    pass


@mcp.command(name='run', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def mcp_run(ctx: click.Context) -> None:
    """Run MCP server."""

    import uvicorn
    from anyio import from_thread
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from starlette.routing import Route

    from dipdup import mcp
    from dipdup.config import DipDupConfig
    from dipdup.config import HttpConfig
    from dipdup.config import McpConfig
    from dipdup.config.http import HttpDatasourceConfig
    from dipdup.context import McpContext
    from dipdup.datasources.http import HttpDatasource
    from dipdup.dipdup import DipDup

    config: DipDupConfig = ctx.obj.config
    dipdup = DipDup(config)

    if not config.mcp:
        config.mcp = McpConfig()
    mcp_config = config.mcp

    api_datasource_config = HttpDatasourceConfig(
        url=mcp_config.default_api_url,
        http=HttpConfig(
            retry_count=0,
        ),
    )
    api_datasource_config._name = 'api'
    api_datasource = HttpDatasource(api_datasource_config)

    mcp_ctx = McpContext._wrap(
        ctx=dipdup._ctx,
        logger=mcp._logger,
        server=mcp.server,
        api=api_datasource,
    )
    mcp.set_ctx(mcp_ctx)

    if mcp_config.compatibility:
        mcp.expose_resources_as_tools()

    # NOTE: Import all submodules to find @dipdup.mcp decorators
    dipdup._ctx.package.verify()

    sse = SseServerTransport('/messages/')

    async def handle_sse(request: Any) -> None:
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp.server.run(
                read_stream=streams[0],
                write_stream=streams[1],
                initialization_options=mcp.server.create_initialization_options(),
                raise_exceptions=True,
            )

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route('/sse', endpoint=handle_sse),
            Mount('/messages/', app=sse.handle_post_message),
        ],
    )

    uv_config = uvicorn.Config(
        app=starlette_app,
        host=mcp_config.host,
        port=mcp_config.port,
        log_config={'version': 1, 'disable_existing_loggers': False},
    )
    server = uvicorn.Server(uv_config)

    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('mcp').setLevel(logging.INFO)

    async def wrapper() -> None:
        async with AsyncExitStack() as stack:
            # NOTE: Create, but don't initialize (no WS loop)
            await dipdup._create_datasources()
            await dipdup._set_up_database(stack)

            # NOTE: Not available in `ctx.datasources`, but directly as `ctx.api`
            await stack.enter_async_context(api_datasource)

            await server.serve()

    # NOTE: Run MCP in a separate thread to avoid blocking the DB connection
    # FIXME: SIGINT ignored
    with from_thread.start_blocking_portal() as portal:
        portal.call(wrapper)


@hasura.command(name='configure', context_settings=CONTEXT_SETTINGS)
@click.option('--force', '-f', is_flag=True, help='Proceed even if Hasura is already configured.')
@click.pass_context
@_cli_wrapper
async def hasura_configure(ctx: click.Context, force: bool) -> None:
    """Configure Hasura GraphQL Engine to use with DipDup."""
    from dipdup.config import DipDupConfig
    from dipdup.config import PostgresDatabaseConfig
    from dipdup.database import tortoise_wrapper
    from dipdup.exceptions import ConfigurationError
    from dipdup.hasura import HasuraGateway

    config: DipDupConfig = ctx.obj.config
    if not config.hasura:
        raise ConfigurationError('`hasura` config section is empty')
    hasura_gateway = HasuraGateway(
        package=config.package,
        hasura_config=config.hasura,
        database_config=cast('PostgresDatabaseConfig', config.database),
    )

    async with AsyncExitStack() as stack:
        await stack.enter_async_context(
            tortoise_wrapper(
                url=config.database.connection_string,
                models=config.package,
                timeout=config.database.connection_timeout,
            )
        )
        await stack.enter_async_context(hasura_gateway)

        await hasura_gateway.configure(force)


@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def schema(ctx: click.Context) -> None:
    """Commands to manage database schema."""
    if any(
        (
            '--help' in sys.argv,
            ctx.invoked_subcommand not in AERICH_CMDS,
            not env.MIGRATIONS,
        )
    ):
        return

    config: DipDupConfig = ctx.obj.config

    if config.database.kind == 'sqlite':
        from dipdup.exceptions import UnsupportedFeatureError

        raise UnsupportedFeatureError('Database migrations are not supported for SQLite')

    from dipdup.package import DipDupPackage

    migrations_dir = DipDupPackage(config.package_path).migrations

    if not migrations_dir.exists():
        from dipdup.exceptions import ProjectPackageError

        raise ProjectPackageError(
            f"""Database migrations are not initialized at {migrations_dir}.
            Run `dipdup schema init` or `dipdup run` to the run the indexer and it'll be initialized automatically."""
        )

    from aerich import Command as AerichCommand  # type: ignore[import-untyped]

    from dipdup.database import get_tortoise_config

    tortoise_config = get_tortoise_config(config.database.connection_string, config.package)
    aerich_command = AerichCommand(tortoise_config=tortoise_config, app='models', location=migrations_dir.as_posix())
    await aerich_command.init()

    ctx.obj['command'] = aerich_command


# NOTE: A wrapper to approve schema after `upgrade` and `downgrade` commands. It would be confusing for the user to run approve just after them.
def _approve_schema_after(command: click.Command) -> click.Command:
    @click.pass_context
    def wrapper(ctx: click.Context, /, *args: Any, **kwargs: Any) -> None:
        ctx.invoke(command, *args, **kwargs)
        # TODO: Don't call approve if no upgrades/downgrades happened
        ctx.invoke(schema_approve)

    return click.Command(
        name=command.name,
        callback=wrapper,
        params=command.params,
        help=command.help,
        short_help=command.short_help,
    )


# NOTE: Saving 0.45s on imports and hiding from reference
if 'schema' in sys.argv:
    try:
        from aerich.cli import cli as aerich_cli  # type: ignore[import-untyped]

        schema.add_command(aerich_cli.commands['history'])
        schema.add_command(aerich_cli.commands['heads'])
        schema.add_command(aerich_cli.commands['migrate'])
        schema.add_command(_approve_schema_after(aerich_cli.commands['upgrade']))
        schema.add_command(_approve_schema_after(aerich_cli.commands['downgrade']))
    except ImportError:
        _logger.debug('aerich is not installed, skipping database migration commands')


@schema.command(name='approve', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def schema_approve(ctx: click.Context) -> None:
    """Continue to use existing schema after reindexing was triggered."""

    from dipdup.database import tortoise_wrapper
    from dipdup.models import Index
    from dipdup.models import Schema

    config: DipDupConfig = ctx.obj.config
    url = config.database.connection_string
    models = f'{config.package}.models'

    _logger.info('Approving schema `%s`', url)

    async with tortoise_wrapper(
        url=url,
        models=models,
        timeout=config.database.connection_timeout,
        decimal_precision=config.advanced.decimal_precision,
    ):
        await Schema.filter(name=config.schema_name).update(
            reindex=None,
            hash=None,
        )
        await Index.filter().update(
            config_hash=None,
        )

    _logger.info('Schema approved')


@schema.command(name='wipe', context_settings=CONTEXT_SETTINGS)
@click.option('--immune', '-i', is_flag=True, help='Drop immune tables too.')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt.')
@click.pass_context
@_cli_wrapper
async def schema_wipe(ctx: click.Context, immune: bool, force: bool) -> None:
    """
    Drop all database tables, functions and views.

    WARNING: This action is irreversible! All indexed data will be lost!
    """
    from dipdup.config import SqliteDatabaseConfig
    from dipdup.exceptions import ConfigurationError

    config: DipDupConfig = ctx.obj.config
    url = config.database.connection_string
    models = f'{config.package}.models'

    # NOTE: Don't be confused by the name of `--immune` flag, we want to drop all tables if it's set.
    immune_tables = set() if immune else config.database.immune_tables

    if isinstance(config.database, SqliteDatabaseConfig):
        message = 'Support for immune tables in SQLite is experimental and requires `advanced.unsafe_sqlite` flag set'
        if config.advanced.unsafe_sqlite:
            immune_tables = immune_tables | ALWAYS_IMMUNE_TABLES
            _logger.warning(message)
        elif immune_tables:
            raise ConfigurationError(message)
    else:
        immune_tables = immune_tables | ALWAYS_IMMUNE_TABLES

    if not force:
        try:
            assert sys.__stdin__.isatty()  # type: ignore[union-attr]
            click.confirm(
                f"You're about to wipe schema `{url}`. All indexed data will be irreversibly lost, are you sure?",
                abort=True,
            )
        except AssertionError:
            echo('Not in a TTY, skipping confirmation')
        except click.Abort:
            echo('\nAborted')
            quit(0)

    _logger.info('Wiping schema `%s`', url)

    from dipdup.database import get_connection
    from dipdup.database import tortoise_wrapper
    from dipdup.database import wipe_schema
    from dipdup.package import DipDupPackage

    migrations_dir = DipDupPackage(config.package_path).migrations

    async with tortoise_wrapper(
        url=url,
        models=models,
        timeout=config.database.connection_timeout,
        decimal_precision=config.advanced.decimal_precision,
        unsafe_sqlite=config.advanced.unsafe_sqlite,
    ):
        conn = get_connection()
        await wipe_schema(
            conn=conn,
            schema_name=(
                config.database.path
                if isinstance(config.database, SqliteDatabaseConfig)
                else config.database.schema_name
            ),
            immune_tables=immune_tables,
            migrations_dir=migrations_dir,
        )

    _logger.info('Schema wiped')


@schema.command(name='init', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def schema_init(ctx: click.Context) -> None:
    """
    Prepare database schema for running DipDup.

    This command creates tables based on your models, then executes `sql/on_reindex` to finish preparation - the same things DipDup does when run on a clean database.
    """
    from dipdup.database import generate_schema
    from dipdup.database import get_connection
    from dipdup.dipdup import DipDup

    config: DipDupConfig = ctx.obj.config
    url = config.database.connection_string
    dipdup = DipDup(config)

    _logger.info('Initializing schema `%s`', url)

    async with AsyncExitStack() as stack:
        await dipdup._set_up_database(stack)
        await dipdup._set_up_hooks()
        await dipdup._create_datasources()
        await dipdup._initialize_schema()
        await dipdup._initialize_migrations()

        # NOTE: It's not necessary a reindex, but it's safe to execute built-in scripts to (re)create views.
        conn = get_connection()
        await generate_schema(
            conn,
            config.database.schema_name,
        )

    _logger.info('Schema initialized')


@schema.command(name='export', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def schema_export(ctx: click.Context) -> None:
    """Print SQL schema including scripts from `sql/on_reindex`.

    This command may help you debug inconsistency between project models and expected SQL schema.
    """

    from tortoise.utils import get_schema_sql

    from dipdup import env
    from dipdup.database import get_connection
    from dipdup.database import tortoise_wrapper
    from dipdup.utils import iter_files

    config: DipDupConfig = ctx.obj.config
    url = config.database.connection_string
    models = f'{config.package}.models'
    package_path = env.get_package_path(config.package)

    async with tortoise_wrapper(
        url=url,
        models=models,
        timeout=config.database.connection_timeout,
        decimal_precision=config.advanced.decimal_precision,
    ):
        conn = get_connection()
        output = get_schema_sql(conn, False) + '\n'
        dipdup_sql_path = Path(__file__).parent / 'sql' / 'on_reindex'
        project_sql_path = package_path / 'sql' / 'on_reindex'

        for sql_path in (dipdup_sql_path, project_sql_path):
            for file in iter_files(sql_path):
                output += file.read() + '\n'

        echo(output)


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.option('--quiet', '-q', is_flag=True, help='Use default values for all prompts.')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing files.')
@click.option(
    '--replay',
    '-r',
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help='Use values from a replay file.',
)
@click.option('--template', '-t', type=str, default=None, help='Use a specific template.')
@click.option('--name', '-n', type=str, default=None, help='Project name.')
@_cli_wrapper
async def new(
    ctx: click.Context,
    quiet: bool,
    force: bool,
    replay: Path | None,
    template: str | None,
    name: str | None,
) -> None:
    """Create a new project interactively."""

    from shutil import which

    from survey._widgets import Escape  # type: ignore[import-untyped]

    from dipdup.config import DipDupConfig
    from dipdup.package import ROOT_CONFIG
    from dipdup.project import answers_from_replay
    from dipdup.project import answers_from_terminal
    from dipdup.project import get_default_answers
    from dipdup.project import render_project
    from dipdup.project import template_from_terminal
    from dipdup.yaml import DipDupYAMLConfig

    config_dict: dict[str, Any] | None = None

    # NOTE: Collect answers from appropriate source
    try:
        if quiet:
            answers = get_default_answers(package=name)
        elif replay:
            answers = answers_from_replay(replay)
        else:
            answers = answers_from_terminal()

            # NOTE: Handle template selection for interactive mode
            if not template:
                template, config_dict = template_from_terminal(answers['package'])

        # NOTE: Priority: CLI arg > interactive selection > default
        template = answers['template'] = template or answers.get('template') or 'demo_blank'

        _logger.info('Using template `%s`', template)
    except Escape:
        return

    _logger.info('Rendering project')
    render_project(answers, force)

    if config_dict:
        # NOTE: Preserve the header at the top of the file
        config_dict = {
            'package': answers['package'],
            'spec_version': '3.0',
            **config_dict,
        }
        path = env.get_package_path(config_dict['package']) / ROOT_CONFIG
        path.write_text(DipDupYAMLConfig(**config_dict).dump())

    _logger.info('Initializing project')
    config = DipDupConfig.load([Path(answers['package'])])
    config.initialize()

    ctx.obj = CLIContext(
        config_paths=[Path(answers['package']).joinpath(ROOT_CONFIG).as_posix()],
        config=config,
    )
    await _cli_unwrapper(init)(
        ctx=ctx,
        base=False,
        force=force,
        no_linter=False,
        no_base=False,
        no_types=False,
        include=[],
    )

    if which('uv'):
        import dipdup.install

        dipdup.install.run_cmd(
            'uv lock',
            shell=True,
            cwd=env.get_package_path(answers['package']),
        )

    green_echo('Project created successfully!')
    green_echo(f'Enter `{answers["package"]}` directory and see README.md for the next steps.')


@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def self(ctx: click.Context) -> None:
    """Commands to manage local DipDup installation."""
    pass


@self.command(name='install', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.option('--quiet', '-q', is_flag=True, help='Use default values for all prompts.')
@click.option('--force', '-f', is_flag=True, help='Force reinstall.')
@click.option('--version', '-v', default=None, help='Install DipDup from specific version.')
@click.option('--ref', '-r', default=None, help='Install DipDup from specific git ref.')
@click.option('--path', '-p', default=None, help='Install DipDup from local path.')
@click.option('--pre', is_flag=True, help='Include pre-release versions.')
@click.option('--editable', '-e', is_flag=True, help='Install DipDup in editable mode.')
@_cli_wrapper
async def self_install(
    ctx: click.Context,
    quiet: bool,
    force: bool,
    version: str | None,
    ref: str | None,
    path: str | None,
    pre: bool,
    editable: bool,
) -> None:
    """Install DipDup for the current user."""
    import dipdup.install
    import dipdup.project

    dipdup.install.install(
        quiet=quiet,
        force=force,
        version=version,
        ref=ref,
        path=path,
        pre=pre,
        editable=editable,
    )


@self.command(name='uninstall', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.option('--quiet', '-q', is_flag=True, help='Use default values for all prompts.')
@_cli_wrapper
async def self_uninstall(
    ctx: click.Context,
    quiet: bool,
) -> None:
    """Uninstall DipDup for the current user."""
    import dipdup.install

    dipdup.install.uninstall(quiet)


@self.command(name='update', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.option('--quiet', '-q', is_flag=True, help='Use default values for all prompts.')
@click.option('--force', '-f', is_flag=True, help='Force reinstall.')
@click.option('--pre', is_flag=True, help='Include pre-release versions.')
@_cli_wrapper
async def self_update(
    ctx: click.Context,
    quiet: bool,
    force: bool,
    pre: bool,
) -> None:
    """Update DipDup for the current user."""
    import dipdup.install
    import dipdup.project

    dipdup.install.install(
        quiet=quiet,
        force=force,
        version=None,
        ref=None,
        path=None,
        pre=pre,
        update=True,
    )


@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def report(ctx: click.Context) -> None:
    """Manage crash and performance reports."""
    from dipdup.report import cleanup_reports

    cleanup_reports()


@report.command(name='ls', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def report_ls(ctx: click.Context) -> None:
    """List reports."""
    from tabulate import tabulate

    from dipdup.report import get_reports
    from dipdup.yaml import yaml_loader

    header = ['id', 'date', 'package', 'reason']
    rows = []
    for path in get_reports():
        event = yaml_loader.load(path)
        row = [
            event['id'],
            event['date'][:-7],
            event['package'],
            event['reason'][:80],
        ]
        rows.append(row)

    rows.sort(key=lambda row: str(row[1]))
    echo(tabulate(rows, headers=header))


@report.command(name='show', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.argument('id', type=str)
@_cli_wrapper
async def report_show(ctx: click.Context, id: str) -> None:
    """Show report."""
    from dipdup.report import REPORTS_PATH
    from dipdup.report import get_reports

    if id == 'latest':
        reports = get_reports()
        if not reports:
            echo('No reports')
            return
        id = reports[-1].stem

    path = REPORTS_PATH / f'{id}.yaml'
    if not path.exists():
        echo('No such report')
        return
    echo(path.read_text())


@report.command(name='rm', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.argument('id', type=str, required=False)
@click.option('--all', '-a', is_flag=True, help='Remove all reports.')
@_cli_wrapper
async def report_rm(ctx: click.Context, id: str | None, all: bool) -> None:
    """Remove report(s)."""
    from dipdup.report import REPORTS_PATH

    if all and id:
        echo('Please specify either name or --all')
        return
    if all:
        path = REPORTS_PATH
        for file in path.iterdir():
            file.unlink()
        return

    path = REPORTS_PATH / f'{id}.yaml'
    if not path.exists():
        echo('No such report')
        return
    path.unlink()


@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def package(ctx: click.Context) -> None:
    """Inspect and manage project package."""
    pass


@package.command(name='tree', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def package_tree(ctx: click.Context) -> None:
    """Draw package tree."""
    from dipdup.package import DipDupPackage
    from dipdup.package import draw_package_tree

    config: DipDupConfig = ctx.obj.config
    package = DipDupPackage(config.package_path)
    package.initialize()

    tree = package.tree()
    echo(f'{package.name} [{package.root}]')
    for line in draw_package_tree(package.root, tree):
        echo(line)


@package.command(name='verify', context_settings=CONTEXT_SETTINGS)
@click.pass_context
@_cli_wrapper
async def package_verify(ctx: click.Context) -> None:
    """Verify project package."""
    from dipdup.package import DipDupPackage

    config: DipDupConfig = ctx.obj.config
    package = DipDupPackage(config.package_path)
    package.initialize()

    package.verify()
