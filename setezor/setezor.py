import atexit
import sys
import os
from contextlib import ExitStack, asynccontextmanager, contextmanager
import tempfile
from dotenv import load_dotenv
from Crypto.Random import get_random_bytes
import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
import click
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from OpenSSL import crypto
load_dotenv()

sys.path[0] = ''
from setezor.exceptions import RequiresLoginException, RequiresProjectException, RequiresRegistrationException
from setezor.settings import STATIC_FILES_DIR_PATH
from setezor.db.alembic import AlembicManager

@asynccontextmanager
async def startup_event(app: FastAPI):
    from setezor.db.database import init_db, fill_db
    await init_db()
    await fill_db()
    yield

def generate_self_signed_cert():
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    cert = crypto.X509()
    cert.get_subject().CN = get_random_bytes(10).hex()
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # 1 year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, "sha256")
    
    return (
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert),
        crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    )


@contextmanager
def temp_ssl_files(cert_pem, key_pem):
    with ExitStack() as stack:
        cert_file = stack.enter_context(
            tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
        )
        key_file = stack.enter_context(
            tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
        )
        cert_file.write(cert_pem)
        key_file.write(key_pem)

        cert_file.flush()
        key_file.flush()
        
        atexit.register(lambda: os.unlink(cert_file.name))
        atexit.register(lambda: os.unlink(key_file.name))
        yield cert_file.name, key_file.name

        
def create_app():
    if not os.environ.get("SERVER_REST_URL", None):
        raise Exception("No SERVER_REST_URL specified")
    from fastapi.responses import RedirectResponse
    from setezor.api import api_routers 
    from setezor.pages import pages_routers
    app = FastAPI(title="Setezor", lifespan=startup_event)
    
    for router in pages_routers:
        app.include_router(router)
    
    for router in api_routers:
        app.include_router(router, prefix="/api/v1")

    app.mount("/static", StaticFiles(directory=STATIC_FILES_DIR_PATH), name="static")

    @app.exception_handler(RequiresLoginException)
    async def login_required(_, __):
        return RedirectResponse('/login')
    
    @app.exception_handler(RequiresRegistrationException)
    async def registration_required(_, __):
        return RedirectResponse('/registration')
    
    @app.exception_handler(RequiresProjectException)
    async def project_required(_, __):
        return RedirectResponse('/projects')

    @app.exception_handler(404)
    async def custom_404_handler(_, __):
        return RedirectResponse("/projects")


    return app


@click.group(chain=False, invoke_without_command=True)
@click.option('-p', '--port', default=16661, type=int, show_default=True, help='Server port')
@click.option('-h', '--host', default="0.0.0.0", type=str, show_default=True, help='Server host')
def run_app(port: int, host: str):
    """Command starts web application"""
    if click.get_current_context().invoked_subcommand is not None: 
        return
    app = create_app()
    with temp_ssl_files(*generate_self_signed_cert()) as (cert_path, key_path):
        uvicorn.run(app=app, 
                    host=host, 
                    port=port, 
                    ssl_keyfile=key_path,
                    ssl_certfile=cert_path)

@run_app.command()
def list_users():
    """Display all users in database"""
    import asyncio
    from setezor.managers.user_manager import UserManager
    from setezor.services import UserProjectService, UsersService, RoleService
    um = UserManager.new_instance(
        users_service=UsersService.new_instance(),
        user_project_service=UserProjectService.new_instance(),
        role_service=RoleService.new_instance(),
    )
    users = asyncio.run(um.list_users())
    print(users)

@run_app.command()
@click.option('-l', '--login', default=False, type=str, help="User's login")
def reset_password(login: str):
    """Resets user's password"""
    import asyncio
    from setezor.managers.user_manager import UserManager
    from setezor.services import UserProjectService, UsersService, RoleService
    um = UserManager.new_instance(
        users_service=UsersService.new_instance(),
        user_project_service=UserProjectService.new_instance(),
        role_service=RoleService.new_instance(),
    )
    result = asyncio.run(um.reset_user_password(login=login))
    print(result)

@run_app.command()
def initial_fill():
    import asyncio
    from setezor.db.database import fill_db
    asyncio.run(fill_db(manual=True))

@run_app.group()
def alembic():
    pass
    """Resets user's password"""
    
@alembic.command()
def history():
    AlembicManager.history()
    
@alembic.command()
def current():
    AlembicManager.current()

@alembic.command()
@click.argument('revision')
def stamp(revision: str):
    AlembicManager.stamp(revision)

@alembic.command()
@click.argument('revision')
def upgrade(revision: str):
    AlembicManager.upgrade(revision)


if __name__ == "__main__":
    run_app()
