from setezor.services.base_service import BaseService
from setezor.models.project import Project
from setezor.schemas.project import SearchVulnsSetTokenForm
from setezor.schemas.roles import Roles


class ProjectService(BaseService):
    async def create(self, new_project: Project):
        async with self._uow:
            new_project_db = self._uow.project.add(new_project.model_dump())
            await self._uow.commit()
            return new_project_db
        
    async def get_by_id(self, project_id: str):
        async with self._uow:
            project = await self._uow.project.find_one(id=project_id)
            return project

    async def delete_by_id(self, user_id: str, project_id: str):
        async with self._uow:
            user_project = await self._uow.user_project.find_one(user_id=user_id, project_id=project_id)
            user_role_in_project = await self._uow.role.find_one(id=user_project.role_id)
            if user_role_in_project.name != Roles.owner:
                return False
            await self._uow.project.delete(id=project_id)
            await self._uow.commit()
            return True
        
    async def set_search_vulns_token(self, project_id: str, token_form: SearchVulnsSetTokenForm):
        async with self._uow:
            project = await self._uow.project.find_one(id=project_id)
            project.search_vulns_token = token_form.token
            await self._uow.commit()
        return None