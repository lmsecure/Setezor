import os

import jinja2
from aiohttp import web
from aiohttp.web import Application
from aiohttp_session import setup as setup_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet
import aiohttp_jinja2
import webbrowser
import nest_asyncio
import click
from colorama import init
from colorama import Fore, Back, Style

from app_routes.api import add_api_routes
from app_routes.pages import add_page_routes
from modules.project_manager.manager import ProjectManager
from modules.application import PMApplication, PMRequest
from app_routes.middlewares import setup_middlewares
from exceptions.loggers import get_logger, LoggerNames
from before_run import check_software

nest_asyncio.apply()
init

base_path = '/'.join(__file__.split('/')[:-1])
PORT = 8008
HOST = '0.0.0.0'

async def create_app(port: int, host = ''):
    project_manager = ProjectManager()
    app = PMApplication(project_manager=project_manager, port=port,
                        base_path=base_path, client_max_size=100*1024*1024)
    key = fernet.Fernet.generate_key()
    crypter = fernet.Fernet(key)
    setup_session(app, EncryptedCookieStorage(crypter))
    add_page_routes(app.router)
    add_api_routes(app.router)
    setup_middlewares(app=app)
    # FixMe there is crutch, need more beautifull solition
    await app.pm.create_mock_project()
    aiohttp_jinja2.setup(app=app, loader=jinja2.FileSystemLoader(os.path.join(base_path, 'app_routes', 'templates')))
    app.router.add_static('/static/', path=os.path.join(base_path, 'static/'), name='static')
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app

async def on_startup(app: Application):
    # check_software(base_path=base_path)
    return
    webbrowser.open_new_tab(f'http://{HOST}:{app.port}')


async def on_shutdown(app: Application):
    pass

def print_banner(host: str, port: int):
    print(Fore.GREEN + f"=========== Start service on http://{host}:{port} ===========" + Style.RESET_ALL)

@click.command()
@click.option('-p', '--port', default=16661, type=int, show_default=True, help='Number of port to binding')
def run_app(port: int):
    web.run_app(app=create_app(port=port), host=HOST, port=port, 
                access_log=get_logger(LoggerNames.web_server, handlers=['file']), 
                print=print_banner(HOST, port))



if __name__ == '__main__':
    run_app()
