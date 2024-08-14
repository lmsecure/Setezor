from aiohttp_session import get_session
from aiohttp.web import Request, Response, HTTPFound, WebSocketResponse

from functools import wraps
from setezor.database.queries import Queries
from .custom_types import WebSocketQueue
from setezor.modules.project_manager.project import Project
from setezor.modules.project_manager.manager import ProjectManager
from setezor.modules.application import PMRequest

def project_require(func):
    """Декоратор, который перенаправляет пользователей на страницу с 
    выбором проекта, если он еще не выбран
    """    
    
    @wraps(func)
    async def wrapped(*args, **kwargs):
        args = list(args)
        if isinstance(args[0], Request):
            request= args[0]
        else:
            request = args[1]
        args.pop(args.index(request))
        session = await get_session(request)
        if session.get('project_id') and session.get('project_id') != '*':
            return await func(request=request, *args, **kwargs)
        else:
            # ToDo redirect to project choosing
            return HTTPFound(location='/projects/')
            
    return wrapped

async def get_db_by_session(request: PMRequest) -> Queries:
    """Метод получения объекта запросов к базу на основе сессии пользователя

    Args:
        request (Request): объект http запроса

    Returns:
        Queries: объект запросов к базе
    """    
    session = await get_session(request=request)
    project_id = session.get('project_id')
    project = await request.app.pm.get_project(project_id)
    db : Queries = project.db
    return db

async def get_configs_by_session(request: PMRequest) -> dict:
    """Метод получения конфигов проекта на основе сессии пользователя

    Args:
        request (Request): объект http запроса

    Returns:
        dict: словарь конфигов проекта
    """    
    session = await get_session(request=request)
    project = await request.app.pm.project_storage.get_project(session.get('project_id'))
    return project.configs

async def get_project(request: PMRequest) -> Project:
    session = await get_session(request=request)
    session.get('user_uuid')
    project_id = session.get('project_id')
    project = await request.app.pm.project_storage.get_project(project_id)
    return project

async def set_websocket_to_client_queue(request: PMRequest, queue_name: str, websocket: WebSocketResponse) -> None:
    project = await get_project(request=request)
    session = await get_session(request=request)
    user_uuid = session.get('user_uuid')
    queue = project.clients.get_queue(user_uuid, queue_name)
    queue.websocket = websocket
    
async def notify_client(request: PMRequest, message: dict, queue_type='message'):
    session = await get_session(request=request,)
    project_manager: ProjectManager = request.app.pm
    await project_manager.notify_single_client(project_id=session.get('project_id'),
                                         client_uuid=session.get('user_uuid'),
                                         message=message,
                                         queue_type=queue_type)
    
async def notify_clients_in_project(request: PMRequest, message: dict, queue_type: str):
    session = await get_session(request=request)
    project_manager: ProjectManager = request.app.pm
    await project_manager.notify_clients(project_id=session.get('project_id'),
                                         message=message,
                                         queue_type=queue_type)
    
