import os
import jinja2
from aiohttp import web
from aiohttp.web import Application
from routes.api import add_api_routes
from routes.pages import add_page_routes
from cryptography import fernet
from aiohttp_session import setup as setup_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_jinja2
from modules.project_manager.manager import ProjectManager
from routes.middlewares import setup_middlewares
from exceptions.loggers import get_logger, LoggerNames
from before_run import check_software
import webbrowser
import nest_asyncio
nest_asyncio.apply()

base_path = '/'.join(__file__.split('/')[:-1])
PORT = 8008
HOST = '0.0.0.0'

async def create_app():
    app = Application(client_max_size=100*1024*1024)
    key = fernet.Fernet.generate_key()
    crypter = fernet.Fernet(key)
    setup_session(app, EncryptedCookieStorage(crypter))
    add_page_routes(app.router)
    add_api_routes(app.router)
    setup_middlewares(app=app)
    app.pm: ProjectManager = ProjectManager()
    # FixMe there is crutch, need more beautifull solition
    app.pm.create_mock_project()
    aiohttp_jinja2.setup(app=app, loader=jinja2.FileSystemLoader(os.path.join(base_path, 'routes', 'templates')))
    app.router.add_static('/static/', path=os.path.join(base_path, 'static/'), name='static')
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.base_path = base_path
    return app

async def on_startup(app: Application):
    check_software(base_path=base_path)
    webbrowser.open_new_tab(f'http://{HOST}:{PORT}')


async def on_shutdown(app: Application):
    pass

def run_app():
    web.run_app(app=create_app(), host=HOST, port=PORT, access_log=get_logger(LoggerNames.web_server, handlers=['file']))


if __name__ == '__main__':
    run_app()
