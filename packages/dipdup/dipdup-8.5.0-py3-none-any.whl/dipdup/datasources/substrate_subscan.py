from typing import Any
from typing import cast

from dipdup.config.substrate_subscan import SubstrateSubscanDatasourceConfig
from dipdup.datasources import AbiDatasource
from dipdup.datasources import AbiJson


class SubstrateSubscanDatasource(AbiDatasource[SubstrateSubscanDatasourceConfig]):
    # FIXME: not used in codegen
    async def get_abi(self, address: str) -> AbiJson:
        raise NotImplementedError

    async def run(self) -> None:
        pass

    async def get_runtime_list(self) -> list[dict[str, Any]]:
        res = await self.request(
            'post',
            'scan/runtime/list',
        )
        return cast('list[dict[str, Any]]', res['data']['list'])

    async def get_runtime_metadata(self, spec_version: int) -> list[dict[str, Any]]:
        res = await self.request(
            'post',
            'scan/runtime/metadata',
            json={'spec': spec_version},
        )
        return cast('list[dict[str, Any]]', res['data']['info']['metadata'])
