from setezor.models import UserProject, Project
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select


class UserProjectRepository(SQLAlchemyRepository[UserProject]):
    model = UserProject


    async def all_projects(self, user_id: int):
        stmt = select(Project).join(UserProject, UserProject.project_id==Project.id).filter(UserProject.user_id==user_id, Project.deleted_at == None)
        result = await self._session.exec(stmt)
        result = result.all()
        return result