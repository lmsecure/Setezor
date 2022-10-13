import os
from aiohttp.web import Application
import jinja2
from aiohttp import web
from routes.api import add_api_routes
from routes.pages import add_page_routes
from cryptography import fernet
from aiohttp_session import setup as setup_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_jinja2
import aiojobs
from routes.middlewares import setup_middlewares
from exceptions.loggers import get_logger, LoggerNames
from before_run import check_software

async def prepare_schedulers(app: web.Application):
    app['schedulers'] = {'scapy': await aiojobs.create_scheduler(limit=1, pending_limit=1),
                         'nmap': await aiojobs.create_scheduler(limit=1, pending_limit=10),
                         'other': await aiojobs.create_scheduler()}

async def create_app():
    app = web.Application(client_max_size=2000000)
    key = fernet.Fernet.generate_key()
    crypter = fernet.Fernet(key)
    setup_session(app, EncryptedCookieStorage(crypter))
    aiohttp_jinja2.setup(app=app, loader=jinja2.FileSystemLoader(os.path.join(os.getcwd(), 'routes', 'templates')))
    await prepare_schedulers(app)
    add_page_routes(app.router)
    add_api_routes(app.router)
    setup_middlewares(app=app)
    app['db'] = {}
    app.router.add_static('/static/', path='static/', name='static')
    return app


if __name__ == '__main__':
    check_software()
    web.run_app(app=create_app(), port=8008, access_log=get_logger(LoggerNames.web_server, handlers=['file']))
