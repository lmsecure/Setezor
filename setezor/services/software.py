
from setezor.services.base_service import BaseService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List, Dict


class SoftwareService(BaseService):
    async def list(self) -> List[Dict]:
        async with self._uow:
            res = await self._uow.software.list()
        result = []
        for software, vendor, version in res:
            result.append(
                {
                    "vendor": vendor.name,
                    **software.model_dump(),
                    "software_version_id": version.id,
                    "version": version.version
                }
            )
        return result

    async def for_search_vulns(self, project_id: str, scan_id: str):
        async with self._uow as uow:
            return await uow.software.for_search_vulns(project_id=project_id,
                                                       scan_id=scan_id)
