
from setezor.interfaces.service import IService
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
    async def is_project_available_for_user(cls, uow: UnitOfWork, project_id: str, user_id: str) -> bool:
        async with uow:
            user_project = await uow.user_project.find_one(user_id=user_id, project_id=project_id)
            return user_project is not None
