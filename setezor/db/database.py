import datetime
import os
from random import randint
from Crypto.Random import get_random_bytes
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from setezor.models import ObjectType, Network_Type, User, Role
from setezor.models.agent import Agent
from setezor.models.base import generate_unique_id
from setezor.models.object import Object

from setezor.settings import DB_URI, PostgresSettings
from setezor.tools.password import PasswordTool
from setezor.logger import logger
from setezor.schemas.roles import Roles
from setezor.schemas.settings import Setting, SettingType

engine = create_async_engine(DB_URI)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

async def init_db():
    if os.environ.get("ENGINE", "sqlite") != "sqlite":
        return
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def fill_db(manual: bool = False):
    if not (os.environ.get("ENGINE", "sqlite") == "sqlite" or manual):
        return
    from setezor.db.uow_dependency import get_uow
    uow = get_uow()
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
                uow.object_type.add(obj.model_dump())
                logger.debug(f"CREATED object {obj.__class__.__name__} {obj.model_dump_json()}")
        await uow.commit()

    async with uow:
        for ID, network_type in [
            ('b271a925283445c5ab60782a42466bfc',"external"), 
            ('08d6fdf488004017b707d42c2cc551b7',"internal"), 
            ('6fa8cc94fce744fb815057c6376666a9',"perimeter")
            ]:
            obj = Network_Type(id=ID, name=network_type)
            if not await uow.network_type.exists(obj):
                uow.network_type.add(obj.model_dump())
                logger.debug(f"CREATED object {obj.__class__.__name__} {obj.model_dump_json()}")
        await uow.commit()

    async with uow:
        user = await uow.user.find_one(login='admin')
        if not user:
            plain_password = get_random_bytes(64).hex()
            print(f"Admin password = {plain_password}")
            new_pwd = PasswordTool.hash(plain_password)
            admin_user = User(
                id=generate_unique_id(),
                created_at=datetime.datetime.now(),
                login="admin",
                hashed_password=new_pwd,
                is_superuser=True,
            )
            uow.user.add(admin_user.model_dump())
            logger.debug(f"CREATED object {admin_user.__class__.__name__} {admin_user.model_dump_json()}")
            

            server_agent = Agent(
                id=generate_unique_id(),
                name="Server",
                description="server",
                rest_url=os.environ.get("SERVER_REST_URL"),
                user_id=admin_user.id,
                is_connected=True
            )
            uow.agent.add(server_agent.model_dump())
        
        await uow.commit()

    async with uow:
        for role_name in Roles:
            role_obj = Role(name=role_name)
            if not await uow.role.exists(role_obj):
                uow.role.add(role_obj.model_dump())
        await uow.commit()


    base_settings = [
        Setting(name="open_reg",
                description="Opened registration",
                value_type=SettingType.boolean,
                field={"value": False})
    ]
    async with uow:
        for setting in base_settings:
            if not await uow.setting.exists(setting):
                uow.setting.add(setting.model_dump())
        await uow.commit()