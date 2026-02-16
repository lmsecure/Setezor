
from setezor.models import Task
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select, desc
from sqlalchemy.engine.result import ScalarResult

class TasksRepository(SQLAlchemyRepository[Task]):
    model = Task


    async def filter(self, *, status, **filter_by):
        stmt = select(self.model).filter(Task.status.in_(status)).filter_by(**filter_by)
        stmt = stmt.order_by(desc(Task.created_at))
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()