import datetime
import os
from random import randint
from Crypto.Random import get_random_bytes
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from setezor.models import ObjectType, Network_Type, User, Role
from setezor.models.agent import Agent
from setezor.models.base import generate_unique_id
from setezor.models.object import Object

from setezor.settings import DB_URI, BASE_PATH, ENGINE
from setezor.tools.password import PasswordTool
from setezor.logger import logger
from setezor.schemas.roles import Roles
from setezor.schemas.settings import Setting, SettingType
from sqlalchemy.pool import NullPool

engine = create_async_engine(DB_URI)
if os.environ.get("PYTEST_VERSION") is not None and os.environ.get("ENGINE", "sqlite") != "sqlite":
    engine = create_async_engine(DB_URI, poolclass=NullPool)
    
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def get_tables_for_triggers() -> list[str]:
    async with engine.begin() as conn:
        def sync_inspect(sync_conn):
            inspector = inspect(sync_conn)
            tables = []
            for table_name in inspector.get_table_names():
                if table_name == 'project':
                    continue
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                if 'deleted_at' in columns and 'project_id' in columns:
                    tables.append(table_name)
            return tables

        return await conn.run_sync(sync_inspect)


async def init_db():
    if os.environ.get("ENGINE", "sqlite") != "sqlite":
        return
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def init_triggers():
    if ENGINE not in ['sqlite', 'postgresql']:
        return
    async with engine.begin() as conn:
        if ENGINE == 'postgresql':
            await conn.execute(
                text(f"""
                    CREATE OR REPLACE FUNCTION soft_delete_project_cascade()
                    RETURNS trigger AS $$
                    DECLARE
                      child RECORD;
                      sql TEXT;
                      parent_table_name TEXT := TG_TABLE_NAME;
                    BEGIN
                      IF NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL THEN
                        FOR child IN
                          EXECUTE format($f$
                            SELECT
                              child_ns.nspname AS child_schema,
                              child.relname AS child_table,
                              child_col.attname AS child_column
                            FROM
                              pg_constraint con
                              JOIN pg_class parent ON con.confrelid = parent.oid
                              JOIN pg_namespace parent_ns ON parent.relnamespace = parent_ns.oid
                              JOIN pg_class child ON con.conrelid = child.oid
                              JOIN pg_namespace child_ns ON child.relnamespace = child_ns.oid
                              JOIN unnest(con.conkey) WITH ORDINALITY AS child_cols(colid, ord) ON TRUE
                              JOIN unnest(con.confkey) WITH ORDINALITY AS parent_cols(colid, ord) ON child_cols.ord = parent_cols.ord
                              JOIN pg_attribute child_col ON (child_col.attrelid = child.oid AND child_col.attnum = child_cols.colid)
                            WHERE
                              con.contype = 'f'
                              AND parent.relname = %L
                          $f$, parent_table_name)
                        LOOP
                          PERFORM 1 FROM information_schema.columns
                           WHERE table_schema = child.child_schema
                             AND table_name = child.child_table
                             AND column_name = 'deleted_at';
                    
                          IF FOUND THEN
                            sql := format(
                              'UPDATE %I.%I SET deleted_at = NOW() WHERE %I = $1 AND deleted_at IS NULL',
                              child.child_schema,
                              child.child_table,
                              child.child_column
                            );
                            EXECUTE sql USING NEW.id;
                          END IF;
                        END LOOP;
                      END IF;
                    
                      RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """)
            )
            await conn.execute(
                text(f"""
                    CREATE OR REPLACE TRIGGER trg_soft_delete_project_cascade
                    BEFORE UPDATE ON project
                    FOR EACH ROW
                    WHEN (OLD.deleted_at IS NULL AND NEW.deleted_at IS NOT NULL)
                    EXECUTE FUNCTION soft_delete_project_cascade();
                """)
            )
        if ENGINE == 'sqlite':
            for table in await get_tables_for_triggers():
                await conn.execute(
                    text(f"""
                        DROP TRIGGER IF EXISTS trg_soft_delete_{table};
                    """)
                )
                await conn.execute(
                    text(f"""
                        CREATE TRIGGER trg_soft_delete_{table}
                        AFTER UPDATE OF deleted_at ON project
                        FOR EACH ROW
                        WHEN NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL
                        BEGIN
                          UPDATE "{table}"
                          SET deleted_at = CURRENT_TIMESTAMP
                          WHERE project_id = NEW.id AND deleted_at IS NULL;
                        END;
                    """)
                )
        await conn.commit()


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