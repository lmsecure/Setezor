from setezor.models import Project#, Scheduler
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select


class ProjectRepository(SQLAlchemyRepository[Project]):
    model = Project


    async def get_schedulers(self, project_id: str):
        stmt = select(Scheduler).filter_by({"project_id":project_id})
        result = await self._session.exec(stmt)
        result = result.all()

    async def generate_schedulers(self, project_id: str):
        stmt = select(Scheduler).filter_by({"project_id":project_id})
        result = await self._session.exec(stmt)
        result = result.all()