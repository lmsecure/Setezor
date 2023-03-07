import os
import jinja2
from aiohttp import web
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
import nest_asyncio
nest_asyncio.apply()


async def create_app():
    app = web.Application(client_max_size=100*1024*1024)
    key = fernet.Fernet.generate_key()
    crypter = fernet.Fernet(key)
    setup_session(app, EncryptedCookieStorage(crypter))
    aiohttp_jinja2.setup(app=app, loader=jinja2.FileSystemLoader(os.path.join('./', 'routes', 'templates')))
    add_page_routes(app.router)
    add_api_routes(app.router)
    setup_middlewares(app=app)
    app.pm: ProjectManager = ProjectManager()
    # FixMe there is crutch, need more beautifull solition
    app.pm.create_mock_project()
    app.router.add_static('/static/', path='static/', name='static')
    return app


if __name__ == '__main__':
    os.chdir(os.path.join(os.environ.get('ORIGIN'), 'usr/src/') if os.environ.get('ORIGIN') else os.getcwd())
    check_software()
    web.run_app(app=create_app(), port=8008, access_log=get_logger(LoggerNames.web_server, handlers=['file']))
