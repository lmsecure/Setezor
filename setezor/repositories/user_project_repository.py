from setezor.models import UserProject, Project, User
from setezor.models.role import Role
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select
from setezor.schemas.roles import Roles


class UserProjectRepository(SQLAlchemyRepository[UserProject]):
    model = UserProject


    async def all_projects(self, user_id: int):
        stmt = select(Project, Role.name).join(UserProject, UserProject.project_id==Project.id).join(Role, Role.id == UserProject.role_id).filter(UserProject.user_id==user_id, Project.deleted_at == None)
        result = await self._session.exec(stmt)
        return result.all()
    
    async def list_project_users(self, project_id):
        stmt = select(User, Role).join(UserProject, User.id == UserProject.user_id).\
        join(Role, UserProject.role_id == Role.id).\
        filter(UserProject.project_id == project_id)
        result = await self._session.exec(stmt)
        return result.all() 
    

    async def get_role_in_project(self, project_id: str, user_id: str):
        stmt = select(Role.name).select_from(UserProject).join(Role, Role.id == UserProject.role_id).filter(UserProject.project_id==project_id, UserProject.user_id==user_id)
        result = await self._session.exec(stmt)
        role_obj = result.first()
        return role_obj