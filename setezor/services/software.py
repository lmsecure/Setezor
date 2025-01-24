
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List, Dict


class SoftwareService(IService):
    @classmethod
    async def list(cls, uow: UnitOfWork) -> List[Dict]:
        async with uow:
            res = await uow.software.list()
        result = []
        for software, vendor in res:
            result.append(
                {
                    "vendor": vendor.name,
                    **software.model_dump(),
                }
            )
        return result