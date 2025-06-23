import os
from setezor.services.base_service import BaseService
from setezor.managers.project_manager.files import FilesStructure, ProjectFolders
from setezor.models.scan import Scan
from setezor.schemas.scan import ScanCreateForm
from setezor.unit_of_work.unit_of_work import UnitOfWork


class ScanService(BaseService):
    async def create(self, project_id: str, scan: ScanCreateForm) -> Scan:
        new_scan_model = Scan(
            name=scan.name,
            description=scan.description,
            project_id=project_id
        )
        async with self._uow:
            new_scan = self._uow.scan.add(new_scan_model.model_dump())
            await self._uow.commit()
        project_path = ProjectFolders.get_path_for_project(project_id=project_id)
        scan_project_path = os.path.join(project_path, new_scan.id)
        FilesStructure.create_project_structure(scan_project_path)
        return new_scan

    async def list(self, project_id: str):
        async with self._uow:
            return await self._uow.scan.filter(project_id=project_id)

    async def get(self, id: str, project_id: str):
        async with self._uow:
            return await self._uow.scan.find_one(id=id, project_id=project_id)
        
    async def get_latest(self, project_id: str) -> Scan:
        async with self._uow:
            return await self._uow.scan.last(project_id=project_id)