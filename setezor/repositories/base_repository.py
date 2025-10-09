from abc import abstractmethod
from typing import Generic, TypeVar, Type, Any, List
import datetime

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func
from sqlmodel import select, update
from sqlalchemy import insert as alc_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from setezor.models import Port, IP, DNS, Domain
from sqlalchemy.engine.result import ScalarResult
from setezor.settings import ENGINE

T = TypeVar("T")


class SQLAlchemyRepository(Generic[T]):

    model: Type[T]

    def __init__(self, session: AsyncSession):
        self._session = session

    def add(self, data: dict) -> T:
        new_instance = self.model(**data)
        self._session.add(new_instance)
        return new_instance

    async def add_with_exists(self, data: dict) -> T:
        if ENGINE == 'sqlite':
            stmt = alc_insert(self.model).values(**data).prefix_with('OR IGNORE')
        elif ENGINE == 'postgresql':
            stmt = pg_insert(self.model).values(**data).on_conflict_do_nothing()
        await self._session.exec(stmt)

    async def add_many(self, data_list: list):
        for data in data_list:
            await self.add_with_exists(data.model_dump())

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

    async def filter_with_deleted_at(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by)
        if hasattr(self.model, 'deleted_at'):
            stmt = stmt.filter(self.model.deleted_at == None)
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()

    async def set_deleted_at(self, id_set: set[str], deleted_at: datetime = None):
        if hasattr(self.model, 'deleted_at'):
            stmt = update(self.model).where(self.model.id.in_(id_set)).values(deleted_at=deleted_at)
            await self._session.exec(stmt)

    async def last(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by).order_by(self.model.created_at.desc())
        res: ScalarResult = await self._session.exec(stmt)
        return res.first()

    @abstractmethod
    async def exists(self, data: T):
        raise NotImplementedError
