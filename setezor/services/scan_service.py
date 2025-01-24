
from setezor.interfaces.service import IService
from setezor.models.scan import Scan
from setezor.schemas.scan import ScanCreateForm
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List, Dict


class ScanService(IService):
    @classmethod
    async def create(cls, uow: UnitOfWork, project_id: str, scan: ScanCreateForm | None = None) -> Scan:
        if not scan:
            scan = ScanCreateForm(
                name="Initial scan"
            )
        new_scan_model = Scan(
            name=scan.name,
            description=scan.description,
            project_id=project_id
        )
        async with uow:
            new_scan = await uow.scan.add(new_scan_model.model_dump())
            await uow.commit()
            return new_scan
        
    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str):
        async with uow:
            return await uow.scan.filter(project_id=project_id)
        
    @classmethod
    async def get(cls, uow: UnitOfWork, id: str):
        async with uow:
            return await uow.scan.find_one(id=id)