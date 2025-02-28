import sys
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
import click
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
load_dotenv()

sys.path[0] = ''
from setezor.exceptions import RequiresLoginException, RequiresProjectException, RequiresRegistrationException
from setezor.settings import PATH_PREFIX, BASE_PATH

if not os.path.exists(PATH_PREFIX):
    os.makedirs(PATH_PREFIX, exist_ok=True)

@asynccontextmanager
async def startup_event(app: FastAPI):
    from setezor.db.database import init_db, fill_db
    await init_db()
    await fill_db()
    yield

def create_app():
    if not os.environ.get("SERVER_REST_URL", None):
        raise Exception("No SERVER_REST_URL specified")
    from fastapi.responses import RedirectResponse
    from setezor.api.routers import api_routers 
    from setezor.pages.routers import pages_routers
    app = FastAPI(title="Setezor", lifespan=startup_event)
    
    for router in pages_routers:
        app.include_router(router)
    
    for router in api_routers:
        app.include_router(router, prefix="/api/v1")

    app.mount("/static", StaticFiles(directory=os.path.join(BASE_PATH, 'pages/static/')), name="static")

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
@click.option('-s', '--spy', default=False, type=bool, show_default=True, help='Enable spy', is_flag=True)
@click.option('-p', '--port', default=16661, type=int, show_default=True, help='Spy port')
@click.option('-h', '--host', default="0.0.0.0", type=str, show_default=True, help='Spy host')
def run_app(spy: bool, port: int, host: str):
    """Command starts web application"""
    if click.get_current_context().invoked_subcommand is not None: 
        return
    if spy:
        from setezor.spy import Spy
        import setezor.managers.task_manager
        app = Spy.create_app()
    else:
        app = create_app()
    uvicorn.run(app=app, 
                host=host, 
                port=port, 
                ssl_keyfile=os.path.join(BASE_PATH, 'key.pem'),
                ssl_certfile=os.path.join(BASE_PATH, 'cert.pem'))

@run_app.command()
def list_users():
    """Display all users in database"""
    import asyncio
    from setezor.managers import UserManager
    users = asyncio.run(UserManager.list_users())
    print(users)

@run_app.command()
@click.option('-l', '--login', default=False, type=str, help="User's login")
def reset_password(login: str):
    """Resets user's password"""
    import asyncio
    from setezor.managers import UserManager
    result = asyncio.run(UserManager.reset_user_password(login=login))
    print(result)

if __name__ == "__main__":
    run_app()
