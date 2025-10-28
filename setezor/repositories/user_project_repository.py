from setezor.models import UserProject, Project, User
from setezor.models.role import Role
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select


class UserProjectRepository(SQLAlchemyRepository[UserProject]):
    model = UserProject
    
    async def all_projects(self, user_id: int):
        owner_subq = (
            select(UserProject.project_id, User.login.label("owner_login"))
            .join(User, User.id == UserProject.user_id)
            .join(Role, Role.id == UserProject.role_id)
            .where(Role.name == "owner")
            .subquery()
        )

        stmt = (
            select(Project, Role.name, owner_subq.c.owner_login)
            .join(UserProject, UserProject.project_id == Project.id)
            .join(Role, Role.id == UserProject.role_id)
            .outerjoin(owner_subq, owner_subq.c.project_id == Project.id)
            .where(UserProject.user_id == user_id, Project.deleted_at.is_(None))
            .distinct()
        )
        result = await self._session.exec(stmt)
        rows = result.all()
        return rows
    
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