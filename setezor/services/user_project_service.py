
from fastapi import HTTPException
from setezor.interfaces.service import IService
from setezor.schemas.user_project import UserChangeRoleInProjectForm
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Project

class UserProjectService(IService):
    @classmethod
    async def get_user_projects(cls, uow: UnitOfWork, user_id: str) -> Project:
        async with uow:
            projects = await uow.user_project.all_projects(user_id=user_id)
            return projects
        
    @classmethod
    async def get_user_project(cls, uow: UnitOfWork, user_id: str, project_id: str) -> Project:
        async with uow:
            return await uow.user_project.find_one(user_id=user_id, project_id=project_id)
    
    @classmethod
    async def list_users_in_project(cls, uow: UnitOfWork, 
                                    user_id: str, project_id: str):
        async with uow:
            users_in_project = await uow.user_project.list_project_users(project_id=project_id)
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
    
    @classmethod
    async def change_user_role_in_project(cls, uow: UnitOfWork,
                                          project_id: str, change_user_role_form: UserChangeRoleInProjectForm):
        async with uow:
            users_in_project = await uow.user_project.find_one(project_id=project_id, user_id=change_user_role_form.user_id)
            if not users_in_project:
                raise HTTPException(status_code=400, detail="User not found in this project")
            await uow.user_project.edit_one(id=users_in_project.id, data={"role_id": change_user_role_form.role_id})
            await uow.commit()

