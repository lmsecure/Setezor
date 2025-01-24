import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

import os
import sys
sys.path[0] = ''
import click
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
import uvicorn
from setezor.exceptions import RequiresLoginException, RequiresProjectException, RequiresRegistrationException
from dotenv import load_dotenv
load_dotenv()


base_path = '/'.join(__file__.split('/')[:-1])
path_prefix = os.path.join(os.path.expanduser('~'), '.local/share/setezor')

if not os.path.exists(path_prefix):
    os.makedirs(path_prefix, exist_ok=True)

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

    app.mount("/static", StaticFiles(directory=os.path.join(base_path, 'pages/static/')), name="static")

    @app.exception_handler(RequiresLoginException)
    async def login_required(_, __):
        return RedirectResponse('/projects')
        return RedirectResponse('/login') # auth_toggled_off
    
    @app.exception_handler(RequiresRegistrationException)
    async def registration_required(_, __):
        return RedirectResponse('/registration')
    
    @app.exception_handler(RequiresProjectException)
    async def project_required(_, __):
        return RedirectResponse('/projects')

    @app.exception_handler(404)
    async def custom_404_handler(_, __):
        return RedirectResponse("/projects_dashboard")


    return app


@click.command()
@click.option('-s', '--spy', default=False, type=bool, show_default=True, help='Enable spy', is_flag=True)
@click.option('-p', '--port', default=16661, type=int, show_default=True, help='Spy port')
def run_app(spy: bool, port: int):
    if spy:
        from setezor.spy import Spy
        import setezor.managers.task_manager
        app = Spy.create_app()
    else:
        app = create_app()
    uvicorn.run(app=app, host="0.0.0.0", port=port, ssl_keyfile=os.path.join(base_path, 'key.pem'), ssl_certfile=os.path.join(base_path, 'cert.pem'))

if __name__ == "__main__":
    run_app()
