
from setezor.models import Task
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select, desc
from sqlalchemy.engine.result import ScalarResult

class TasksRepository(SQLAlchemyRepository[Task]):
    model = Task


    async def filter(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by).order_by(desc(Task.created_at))
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()