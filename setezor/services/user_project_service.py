
from fastapi import HTTPException
from setezor.services.base_service import BaseService
from setezor.models.user_project import UserProject
from setezor.schemas.user_project import UserChangeRoleInProjectForm
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Project

class UserProjectService(BaseService):

    async def create(self, new_user_project: UserProject):
        async with self._uow:
            user_project = self._uow.user_project.add(new_user_project.model_dump())
            await self._uow.commit()
            return user_project

    async def get_user_projects(self, user_id: str) -> Project:
        async with self._uow:
            projects = await self._uow.user_project.all_projects(user_id=user_id)
            return projects
        

    async def get_user_project(self, user_id: str, project_id: str) -> Project:
        async with self._uow:
            return await self._uow.user_project.find_one(user_id=user_id, project_id=project_id)
    

    async def list_users_in_project(self, 
                                    user_id: str, project_id: str):
        async with self._uow:
            users_in_project = await self._uow.user_project.list_project_users(project_id=project_id)
        result = []
        for user, role in users_in_project:
            if user.id != user_id:
                result.append({
                    "id": user.id,
                    "login": user.login,
                    "role_id": role.id,
                    "role": role.name
                })
        return result
    
    async def change_user_role_in_project(self,
                                          project_id: str, change_user_role_form: UserChangeRoleInProjectForm):
        async with self._uow:
            users_in_project = await self._uow.user_project.find_one(project_id=project_id, user_id=change_user_role_form.user_id)
            if not users_in_project:
                raise HTTPException(status_code=400, detail="User not found in this project")
            await self._uow.user_project.edit_one(id=users_in_project.id, data={"role_id": change_user_role_form.role_id})
            await self._uow.commit()

