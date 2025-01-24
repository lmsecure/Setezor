import datetime
from asyncio import current_task
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, async_scoped_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from setezor.models import ObjectType, Network_Type, User
import setezor.unit_of_work as UOW
from setezor.setezor import path_prefix


engine = create_async_engine(f"sqlite+aiosqlite:///{path_prefix}/db.sqlite3")
#engine = create_async_engine("postgresql+asyncpg://test:test@localhost:5432/test")
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

async def init_db():
    async with engine.begin() as conn:
        #await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def fill_db():
    uow = UOW.UnitOfWork()
    async with uow:
        for new_id, obj_type in [
            ('3d9cf6c43fd54aacb88878f5425f43c4','unknown') ,
            ('0f53be90b5534091844969585a109ccc','router') ,
            ('5a3edb2b46dd43a38a62d15263204512','switch') ,
            ('50eabecb80f345709c55fea37106ff4c','win_server') ,
            ('9931d00b80264046a2a2729c190110a8','linux_server') ,
            ('0391e3dd460241eea140dd0bf2786c84','firewall') ,
            ('5794843deda7454dbad181a012f8f914','win_pc') ,
            ('73b6106cc1fa4f129683548f3f2d3184','linux_pc') ,
            ('4681b1c682a0445b8242a0cfa3888b86','nas') ,
            ('2a2713215d624cb7a74c6918e37e2ecf','ip_phone') ,
            ('f3cc1e8288ef46a6a0355061fb1272f3','printer') ,
            ('0a295b4782384fa895effe7f89fc0fc8','tv') ,
            ('2489848fd5a342fdb75881c6e2c7b30f','android_device'),
            ]:  
            obj = ObjectType(id=new_id, name=obj_type)
            if not await uow.object_type.exists(obj):
                uow.session.add(obj)
        await uow.commit()

    async with uow:
        for ID, network_type in [
            ('b271a925283445c5ab60782a42466bfc',"external"), 
            ('08d6fdf488004017b707d42c2cc551b7',"internal"), 
            ('6fa8cc94fce744fb815057c6376666a9',"perimeter")
            ]:
            obj = Network_Type(id=ID, name=network_type)
            if not await uow.network_type.exists(obj):
                uow.session.add(obj)
        await uow.commit()

    async with uow:
        user = await uow.user.find_one(id='deadbeefdeadbeefdeadbeefdeadbeef')
        if not user:
            admin_user = User(
                id='deadbeefdeadbeefdeadbeefdeadbeef',
                created_at=datetime.datetime.now(),
                login="admin",
                hashed_password="$pbkdf2-sha256$300000$59ybU2qtVcrZe..ds5bSGg$ABaTk2qmQJ8pp40a9eXOKrpQmamIO5VDSzk4rQlCGNU"
            )
            uow.session.add(admin_user)
        await uow.commit()