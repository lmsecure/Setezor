from abc import abstractmethod
from typing import Generic, TypeVar, Type, Any
import datetime

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, update
from sqlalchemy.engine.result import ScalarResult
from sqlmodel import SQLModel

T = TypeVar("T")


class SQLAlchemyRepository(Generic[T]):

    model: Type[T]

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, data: dict) -> T:
        new_instance = self.model(**data)
        self._session.add(new_instance)
        return new_instance

    async def edit_one(self, id: int, data: dict):
        stmt = update(self.model).values(
            **data).filter_by(id=id).returning(self.model.id)
        res: ScalarResult = await self._session.exec(stmt)
        return res.one()

    async def delete(self, id: Any):
        stmt = update(self.model).values(deleted_at=datetime.datetime.now()).filter_by(id=id).returning(self.model.id)
        res: ScalarResult = await self._session.exec(stmt)
        return res.one()

    async def list(self):
        stmt = select(self.model)
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()

    async def find_one(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by)
        res: ScalarResult = await self._session.exec(stmt)
        return res.first()

    async def filter(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by)
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()

    async def last(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by).order_by(self.model.created_at.desc())
        res: ScalarResult = await self._session.exec(stmt)
        return res.first()

    @abstractmethod
    async def exists(self, data: T):
        raise NotImplementedError
