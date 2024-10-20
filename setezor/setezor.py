import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

import os
import ssl
from pathlib import Path

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

import sys
sys.path[0] = ''

from setezor.app_routes.api import add_api_routes
from setezor.app_routes.pages import add_page_routes
from setezor.modules.project_manager.manager import ProjectManager
from setezor.modules.application import PMApplication, PMRequest
from setezor.app_routes.middlewares import setup_middlewares
from setezor.exceptions.loggers import get_logger, LoggerNames
from setezor.before_run import check_software
from setezor.spy import spy as spy_instanse

nest_asyncio.apply()
init()

base_path = '/'.join(__file__.split('/')[:-1])
PORT = 8008
HOST = '0.0.0.0'


async def create_app(port: int, host = ''):
    project_manager = ProjectManager()
    app = PMApplication(project_manager=project_manager, port=port,
                        base_path=base_path, client_max_size=100*1024*1024)
    await project_manager.setup()
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
    print(Fore.GREEN + f"=========== Start service on https://{host}:{port} ===========" + Style.RESET_ALL)

def create_ssl_context():
    path = Path(__file__).absolute()
    cert = path.parent / Path('cert.pem')
    key = path.parent / Path('key.pem')
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=cert, keyfile=key)
    return ssl_context

@click.command()
@click.option('-p', '--port', default=16661, type=int, show_default=True, help='Number of port to binding')
@click.option('-s', '--spy', default=False, type=bool, show_default=True, help='Enable spy', is_flag=True)
def run_app(port: int, spy: bool):
    if spy:
        spy_instanse.serve(host=HOST, port=port)
    else:
        web.run_app(app=create_app(port=port), host=HOST, port=port, 
                    access_log=get_logger(LoggerNames.web_server, handlers=['file']), 
                    print=print_banner(HOST, port),
                    ssl_context=create_ssl_context())



if __name__ == '__main__':
    run_app()
