import os
import jinja2
from aiohttp.web import Application
from app_routes.api import add_api_routes
from app_routes.pages import add_page_routes
from cryptography import fernet
from aiohttp_session import setup as setup_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_jinja2
from modules.project_manager.manager import ProjectManager
from app_routes.middlewares import setup_middlewares
from before_run import check_software
import webbrowser
import nest_asyncio
nest_asyncio.apply()
from colorama import init
init
from colorama import Fore, Back, Style


base_path = '/'.join(__file__.split('/')[:-1])


async def create_app(host: str, port: int):
    app = Application(client_max_size=100*1024*1024)
    app.port = port
    app.host = host
    key = fernet.Fernet.generate_key()
    crypter = fernet.Fernet(key)
    setup_session(app, EncryptedCookieStorage(crypter))
    add_page_routes(app.router)
    add_api_routes(app.router)
    setup_middlewares(app=app)
    app.pm: ProjectManager = ProjectManager()
    # FixMe there is crutch, need more beautifull solition
    app.pm.create_mock_project()
    aiohttp_jinja2.setup(app=app, loader=jinja2.FileSystemLoader(os.path.join(base_path, 'app_routes', 'templates')))
    app.router.add_static('/static/', path=os.path.join(base_path, 'static/'), name='static')
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.base_path = base_path
    return app

async def on_startup(app: Application):
    # check_software(base_path=base_path)
    webbrowser.open_new_tab(f'http://{app.host}:{app.port}')


async def on_shutdown(app: Application):
    pass

def print_banner(host: str, port: int):
    print(Fore.GREEN + f"=========== Start service on http://{host}:{port} ===========" + Style.RESET_ALL)