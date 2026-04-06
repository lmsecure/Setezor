from setezor.schemas.roles import Roles
from setezor.models import UserProject, Project, User, Role
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select
from sqlalchemy.orm import aliased


class UserProjectRepository(SQLAlchemyRepository[UserProject]):
    model = UserProject


    async def all_projects(self, user_id: int):
        user_project_1 = aliased(UserProject)
        user_project_2 = aliased(UserProject)
        role_1 = aliased(Role)
        role_2 = aliased(Role)
        user_1 = aliased(User)
        user_2 = aliased(User)

        stmt = (
            select(
                user_project_1.project_id,
                Project.name.label("project_name"),
                user_1.login,
                role_1.name.label("role"),
                user_2.login.label("owner_login"),
            )
            .select_from(user_project_1)
            .join(Project, user_project_1.project_id == Project.id)
            .join(role_1, user_project_1.role_id == role_1.id)
            .join(user_1, user_project_1.user_id == user_1.id)
            .join(user_project_2, user_project_1.project_id == user_project_2.project_id)
            .join(role_2, user_project_2.role_id == role_2.id)
            .join(user_2, user_project_2.user_id == user_2.id)
            .where(
                user_1.id == user_id,
                role_2.name == Roles.owner,
                Project.deleted_at.is_(None)
            )
        )

        result = await self._session.exec(stmt)
        return [dict(row) for row in result.mappings()]


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