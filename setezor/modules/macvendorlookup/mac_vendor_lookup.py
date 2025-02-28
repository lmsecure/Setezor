import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from .models import Base, MacVendor
from .data_collector import DataCollector



class MacVendorLookup:
    _path = f"{os.path.dirname(__file__)}/mac_vendor.sqlite3"
    engine = create_async_engine(f"sqlite+aiosqlite:///{_path}", echo=False)
    commit_step = 1000

    @classmethod
    async def create_db(cls):
        if os.path.exists(cls._path):
            os.remove(cls._path)
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @classmethod
    async def get_session(cls) -> AsyncSession:
        AsyncSessionMaker = sessionmaker(bind=cls.engine,
                                        class_=AsyncSession,
                                        expire_on_commit=False)
        return AsyncSessionMaker()

    def session_provide(func):
        async def wrapper(cls, *args, **kwargs):
            session = await cls.get_session()
            try:
                result = await func(cls, session, *args, **kwargs)
            finally:
                await session.close()
            return result
        return wrapper

    @classmethod
    async def update_db(cls):
        await cls.create_db()
        session = await cls.get_session()
        data = await DataCollector.get_data()
        for i in range(0, len(data), cls.commit_step):
            session.add_all(data[i:i+cls.commit_step])
            await session.flush()
        await session.commit()
        await session.close()

    @classmethod
    @session_provide
    async def get_obj(cls, session: AsyncSession, column: str, value) -> dict:
        stmt = select(MacVendor).filter(getattr(MacVendor, column) == value)
        result = await session.execute(stmt)
        result = result.first()
        if result:
            return result[0].to_dict()
        return {}

    @classmethod
    async def get_vendor_from_mac(cls, mac: str) -> str:
        mac_prefix = mac.translate(str.maketrans('', '', ':-'))[:6].upper()
        result_obj = await cls.get_obj(column="mac_prefix", value=mac_prefix)
        return result_obj.get("vendor", "")
