from aiohttp_session import get_session
from aiohttp.web import Request, Response, HTTPFound
from functools import wraps
from database.queries import Queries


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
        if session.get('project_name'):
            return await func(request=request, *args, **kwargs)
        else:
            # ToDo redirect to project choosing
            return HTTPFound(location='/projects/')
            
    return wrapped

async def get_db_by_session(request: Request) -> Queries:
    """Метод получения объекта запросов к базу на основе сессии пользователя

    Args:
        request (Request): объект http запроса

    Returns:
        Queries: объект запросов к базе
    """    
    session = await get_session(request=request)
    project_name = session.get('project_name')
    db : Queries = request.app['db'].get(project_name)
    return db

async def get_configs_by_session(request: Request) -> dict:
    """Метод получения конфигов проекта на основе сессии пользователя

    Args:
        request (Request): объект http запроса

    Returns:
        dict: словарь конфигов проекта
    """    
    session = await get_session(request=request)
    return session.get('project_config')
