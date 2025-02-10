from setezor.schemas.port import PortSchema, PortSchemaAdd
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List


class PortService(IService):
    @classmethod
    async def create(cls, uow: UnitOfWork, port: PortSchemaAdd) -> int:
        port_dict = port.model_dump()
        async with uow:
            port_id = uow.port.add(port_dict)
            await uow.commit()
            return port_id

    @classmethod
    async def list(cls, uow: UnitOfWork) -> List[PortSchema]:
        async with uow:
            ports = await uow.port.list()
            return ports

    @classmethod
    async def get(cls, uow: UnitOfWork, id: int) -> PortSchema:
        async with uow:
            port = await uow.port.find_one(id=id)
            return port
