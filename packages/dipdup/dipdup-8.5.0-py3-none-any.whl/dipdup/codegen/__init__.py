import logging
from abc import ABC
from abc import abstractmethod
from collections import deque
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Iterator
from pathlib import Path
from shutil import rmtree
from typing import Any
from typing import final

from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from dipdup import env
from dipdup.config import SYSTEM_HOOKS
from dipdup.config import DipDupConfig
from dipdup.config import HandlerConfig
from dipdup.config import IndexTemplateConfig
from dipdup.config._mixin import CallbackMixin
from dipdup.datasources import AbiDatasource
from dipdup.datasources import AbiJson
from dipdup.datasources import ContractConfigT
from dipdup.datasources import Datasource
from dipdup.datasources import DatasourceConfigT
from dipdup.exceptions import AbiNotAvailableError
from dipdup.exceptions import ConfigurationError
from dipdup.exceptions import DatasourceError
from dipdup.package import KEEP_MARKER
from dipdup.package import PACKAGE_MARKER
from dipdup.package import DipDupPackage
from dipdup.project import CODEGEN_HEADER
from dipdup.project import render_base
from dipdup.utils import load_template
from dipdup.utils import pascal_to_snake
from dipdup.utils import sorted_glob
from dipdup.utils import touch
from dipdup.utils import write

Callback = Callable[..., Awaitable[None]]
TypeClass = type[BaseModel]

_logger = logging.getLogger(__name__)


@dataclass
class BatchHandlerConfig(HandlerConfig, CallbackMixin):
    name: str = 'batch'
    callback: str = 'batch'

    def iter_imports(self, package: str) -> Iterator[tuple[str, str]]:
        yield 'dipdup.context', 'HandlerContext'
        yield 'dipdup.index', 'MatchedHandler'

    def iter_arguments(self) -> Iterator[tuple[str, str]]:
        yield 'ctx', 'HandlerContext'
        yield 'handlers', 'tuple[MatchedHandler, ...]'


class _BaseCodeGenerator(ABC):
    def __init__(
        self,
        config: DipDupConfig,
        package: DipDupPackage,
        datasources: dict[str, Datasource[Any]],
        include: set[str] | None = None,
    ) -> None:
        self._config = config
        self._package = package
        self._datasources = datasources
        self._include = include or set()
        self._logger = _logger

    @abstractmethod
    async def init(
        self,
        force: bool = False,
        no_linter: bool = False,
        no_base: bool = False,
    ) -> None: ...

    async def _generate_callback(
        self,
        callback_config: CallbackMixin,
        kind: str,
        sql: bool = False,
        code: tuple[str, ...] = (),
    ) -> None:
        original_callback = callback_config.callback
        subpackages = callback_config.callback.split('.')
        subpackages, callback = subpackages[:-1], subpackages[-1]

        callback_path = Path(
            self._package.root,
            kind,
            *subpackages,
            f'{callback}.py',
        )

        if callback_path.exists():
            return

        self._logger.info('Generating %s callback `%s`', kind, callback)
        callback_template = load_template('templates', 'callback.py.j2')

        arguments = callback_config.format_arguments()
        imports = set(callback_config.format_imports(self._config.package))

        code_deque: deque[str] = deque(code)
        if sql:
            code_deque.append(f"await ctx.execute_sql_script('{original_callback}')")
            # FIXME: move me
            if callback == 'on_index_rollback':
                code_deque.append('await ctx.rollback(')
                code_deque.append('    index=index.name,')
                code_deque.append('    from_level=from_level,')
                code_deque.append('    to_level=to_level,')
                code_deque.append(')')

        if not code_deque:
            code_deque.append('...')

        # FIXME: Missing generic type annotation to comply with `mypy --strict`
        processed_arguments = tuple(
            f'{a},  # type: ignore[type-arg]' if a.startswith('index: Index') else a for a in arguments
        )

        callback_code = callback_template.render(
            callback=callback,
            arguments=tuple(processed_arguments),
            imports=sorted(dict.fromkeys(imports)),
            code=code_deque,
        )
        write(callback_path, callback_code)

        if not sql:
            return

        # NOTE: Preserve the same structure as in `handlers`
        sql_path = Path(
            self._package.sql,
            *subpackages,
            callback,
            KEEP_MARKER,
        )
        touch(sql_path)


class CodeGenerator(_BaseCodeGenerator, ABC):
    """Base class for blockchain-specific code generators."""

    kind: str

    @property
    def schemas_dir(self) -> Path:
        return self._package.schemas / self.kind

    @abstractmethod
    async def generate_abis(self) -> None: ...

    @abstractmethod
    async def generate_schemas(self) -> None: ...

    @abstractmethod
    def get_typeclass_name(self, schema_path: Path) -> str: ...

    async def init(
        self,
        force: bool = False,
        no_linter: bool = False,
        no_base: bool = False,
    ) -> None:
        _logger.info('%s: generating ABIs', self.kind)
        await self.generate_abis()

        _logger.info('%s: generating JSONSchemas', self.kind)
        await self.generate_schemas()

        _logger.info('%s: generating types', self.kind)
        await self._generate_types(force)

    async def _generate_types(self, force: bool = False) -> None:
        """Generate typeclasses from fetched JSONSchemas: contract's storage, parameters, big maps and events."""
        for path in sorted_glob(self.schemas_dir, '**/*.json'):
            await self._generate_type(path, force)

    async def _generate_type(self, schema_path: Path, force: bool) -> None:
        rel_path = schema_path.relative_to(self.schemas_dir)
        type_pkg_path = self._package.types / rel_path

        if schema_path.is_dir():
            return

        if not schema_path.name.endswith('.json'):
            if schema_path.name != KEEP_MARKER:
                self._logger.warning('Skipping `%s`: not a JSON schema', schema_path)
            return

        module_name = schema_path.stem
        output_path = type_pkg_path.parent / f'{pascal_to_snake(module_name)}.py'
        if output_path.exists() and not force:
            self._logger.debug('Skipping `%s`: type already exists', schema_path)
            return

        import datamodel_code_generator as dmcg

        class_name = self.get_typeclass_name(schema_path)
        self._logger.info('Generating type `%s`', class_name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # TODO: make it configurable
        if 'substrate' in str(output_path):
            model_type = dmcg.DataModelType.TypingTypedDict
        else:
            model_type = dmcg.DataModelType.PydanticV2BaseModel
        dmcg.generate(
            input_=schema_path,
            output=output_path,
            class_name=class_name,
            disable_timestamp=True,
            input_file_type=dmcg.InputFileType.JsonSchema,
            target_python_version=dmcg.PythonVersion.PY_312,
            custom_file_header=CODEGEN_HEADER,
            use_union_operator=True,
            output_model_type=model_type,
            use_schema_description=True,
        )

    def _cleanup_schemas(self) -> None:
        rmtree(self.schemas_dir, ignore_errors=True)

    async def _lookup_abi(
        self,
        contract: ContractConfigT,
        datasources: list[AbiDatasource[DatasourceConfigT]],
    ) -> AbiJson:
        """For every contract goes over each datasourse and tries to obtain abi file.
        If no ABI exists for any of the contracts - raises error.
        """
        address = contract.address or contract.abi
        if not address:
            raise ConfigurationError(f'`address` or `abi` must be specified for contract `{contract.module_name}`')

        for datasource in datasources:
            try:
                return await datasource.get_abi(address=address)
            except DatasourceError as e:
                _logger.warning('Failed to fetch ABI from `%s`: %s', datasource.name, e)

        raise AbiNotAvailableError(
            address=address,
            typename=contract.module_name,
        )


@final
class CommonCodeGenerator(_BaseCodeGenerator):
    async def init(
        self,
        force: bool = False,
        no_linter: bool = False,
        no_base: bool = False,
    ) -> None:
        # NOTE: Package structure
        self._package.initialize()

        # NOTE: Common files
        if not (env.NO_BASE or no_base):
            _logger.info('Recreating base template with replay.yaml')
            render_base(
                answers=self._package.replay,
                force=force,
                include=self._include,
            )

        await self.generate_models()

        await self.generate_hooks()
        await self.generate_system_hooks()

        # NOTE: Callback stubs
        await self.generate_handlers()
        await self.generate_batch_handler()

    async def generate_models(self) -> None:
        for path in self._package.models.glob('**/*.py'):
            if path.stat().st_size == 0:
                continue
            return

        path = self._package.models / PACKAGE_MARKER
        content_path = Path(__file__).parent.parent / 'templates' / 'models.py'
        write(path, content_path.read_text())

    async def generate_hooks(self) -> None:
        for hook_config in self._config.hooks.values():
            await self._generate_callback(hook_config, 'hooks', sql=True)

    async def generate_system_hooks(self) -> None:
        for hook_config in SYSTEM_HOOKS.values():
            await self._generate_callback(hook_config, 'hooks', sql=True)

    async def generate_handlers(self) -> None:
        for index_config in self._config.indexes.values():
            if isinstance(index_config, IndexTemplateConfig):
                continue

            for handler_config in index_config.handlers:
                await self._generate_callback(handler_config, 'handlers')

    async def generate_batch_handler(self) -> None:
        await self._generate_callback(
            callback_config=BatchHandlerConfig(),
            kind='handlers',
            code=(
                'for handler in handlers:',
                '    await ctx.fire_matched_handler(handler)',
            ),
        )
