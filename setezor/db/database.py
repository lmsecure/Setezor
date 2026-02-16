import datetime
import os
import sqlite3

import psycopg
from Crypto.Random import get_random_bytes
from psycopg.errors import UndefinedTable
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from setezor.models import ObjectType, Network_Type, User, Role
from setezor.models import Agent, AgentInterface
from setezor.models.base import generate_unique_id
from setezor.models.d_dns_type import DNS_Type

from setezor.settings import DB_URI, ENGINE, DEV, PORT, SERVER_REST_URL
from setezor.tools.password import PasswordTool
from setezor.logger import logger
from setezor.schemas.roles import Roles
from setezor.schemas.settings import Setting, SettingType
from sqlalchemy.pool import NullPool
from .entities import ObjectTypes, NetworkTypes, DNSTypes


engine = create_async_engine(DB_URI)
if os.environ.get("PYTEST_VERSION") is not None and os.environ.get("ENGINE", "sqlite") != "sqlite":
    engine = create_async_engine(DB_URI, poolclass=NullPool)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def get_db_tables():
    async with engine.begin() as conn:
        def get_tables(sync_conn):
            inspector = inspect(sync_conn)
            return inspector.get_table_names()
        return await conn.run_sync(get_tables)


async def init_db():
    tables = await get_db_tables()
    if not tables:
        logger.info("the database is not initialized")
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("the database is initialized")
        await fill_db()


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


async def create_triggers(conn):
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
        await conn.execute(
            text(f"""
                CREATE OR REPLACE TRIGGER trg_soft_delete_project_scope_cascade
                BEFORE UPDATE ON project_scope
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
        await conn.execute(
            text(f"""
                DROP TRIGGER IF EXISTS trg_soft_delete_for_project_scope;
            """)
        )
        await conn.execute(
            text(f"""
                CREATE TRIGGER trg_soft_delete_for_project_scope
                AFTER UPDATE OF deleted_at ON project_scope
                FOR EACH ROW
                WHEN NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL
                BEGIN
                  UPDATE project_scope_targets
                  SET deleted_at = CURRENT_TIMESTAMP
                  WHERE project_id = NEW.project_id AND deleted_at IS NULL;
                END;
            """)
        )
    await conn.commit()


async def reset_db():
    async with engine.begin() as conn:
        if engine.dialect.name == 'postgresql':
            await conn.execute(text('DROP SCHEMA public CASCADE'))
            await conn.execute(text('CREATE SCHEMA public'))
        else:
            await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        await create_triggers(conn)


async def init_triggers():
    if ENGINE not in ['sqlite', 'postgresql']:
        return

    async with engine.begin() as conn:
        await create_triggers(conn)




async def fill_db(manual: bool = False):
    from setezor.db.uow_dependency import get_uow
    uow = get_uow()
    async with uow:
        for obj_type in ObjectTypes:
            obj = ObjectType(id=obj_type.value, name=obj_type.name)
            if not await uow.object_type.exists(obj):
                uow.object_type.add(obj.model_dump())
                logger.debug(f"CREATED object {obj.__class__.__name__} {obj.model_dump_json()}")
        await uow.commit()

    async with uow:
        for network_type in NetworkTypes:
            obj = Network_Type(id=network_type.value, name=network_type.name)
            if not await uow.network_type.exists(obj):
                uow.network_type.add(obj.model_dump())
                logger.debug(f"CREATED object {obj.__class__.__name__} {obj.model_dump_json()}")
        await uow.commit()

    async with uow:
        for dns_type in DNSTypes:
            obj = DNS_Type(id=dns_type.value, name=dns_type.name)
            if not await uow.dns_type.exists(obj):
                uow.dns_type.add(obj.model_dump())
                logger.debug(f"CREATED object {obj.__class__.__name__} {obj.model_dump_json()}")
        await uow.commit()

    async with uow:
        admin_user = await uow.user.find_one(login='admin')
        if not admin_user:
            plain_password = get_random_bytes(64).hex()
            if DEV.mode:
                DEV.password = plain_password
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
            rest_url=SERVER_REST_URL,
            user_id=admin_user.id,
            is_connected=True
        )
        uow.agent.add(server_agent.model_dump())

        synthetic_agent = Agent(
            id=generate_unique_id(),
            name="Synthetic",
            description="Not for active scans",
            rest_url="",
            user_id=admin_user.id,
            is_connected=True
        )
        uow.agent.add(synthetic_agent.model_dump())

        synthetic_interface = AgentInterface(
            id=generate_unique_id(),
            agent_id=synthetic_agent.id,
            name="Default",
            ip="127.0.0.1",
            mac="00:DE:AD:BE:AF:00",
            is_default=True
        )
        uow.agent_interface.add(synthetic_interface.model_dump())

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

    logger.info("initial data has been loaded into the database")


def check_server_port() -> int:
    try:
        query = "SELECT rest_url from setezor_agent WHERE name = 'Server';"
        if ENGINE == 'postgresql':
            with psycopg.connect(DB_URI.replace('+asyncpg', '')) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    row = cur.fetchone()
        else:
            db_path = DB_URI.replace('+aiosqlite', '')
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                cur.execute(query)
                row = cur.fetchone()

        try:
            server_port = int(row[0].rsplit(':')[-1]) if row else PORT
            if server_port != PORT:
                logger.warning(f"===================================================="
                               f"\nServer port in .env mismatch with port in database. "
                               f"\nWill be used DB port {server_port}\n"
                               f"====================================================")
        except ValueError:
            return PORT
        return server_port
    except (UndefinedTable, sqlite3.OperationalError):
        return PORT
