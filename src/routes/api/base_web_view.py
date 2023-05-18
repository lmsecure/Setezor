from aiohttp.web import Response, Request, json_response
from abc import ABC, abstractmethod
from database.queries_files.base_queries import BaseQueries
from functools import wraps
from routes.session import get_db_by_session, notify_client
import json


class BaseView(ABC):
    """Базовый api класс 
    """
    
    queries_path: str
    
    def __init__(self, path: str):
        """Инициализация класса api

        Args:
            path (str): _description_
        """        
        self.endpoint = path + self.endpoint
    
    def route(method, path):
        """Декоратор с аргументами, который при вызове возвращает словарь
        для добавления метода в routes aiohttp server

        Args:
            method (_type_): тип HTTP метода
            path (_type_): конечное uri ендпоинта
        """
        def wrapped(func):
            def route_wrapper(obj):
                def wr1(*args, **kwargs):
                    return func(obj, *args, **kwargs)
                return {'method': method, 'path': obj.endpoint + path, 'handler': wr1}
            return route_wrapper
        return wrapped
    
    @route('POST', '/from_table')
    async def create_from_table(self, request: Request) -> Response:
        """Метод создания объекта в базе со страницы info

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """
        db_entity = await self.get_db_queries(request=request)
        params = await request.json()
        params.pop('id')
        db_entity.simple_create(**params)
        await notify_client(request=request, message={'title': 'Record created', 'type': 'info',
                                                      'text': f'Create "{self.queries_path.capitalize()}" with params {json.dumps(params, ensure_ascii=False)}'})
        return json_response(status=200, data={'message': 'Added'})
    
    @route('POST', '/')
    async def create(self, request: Request) -> Response:
        return Response(status=404, text='Error: Method not implement')
    
    @route('DELETE', '/')
    async def delete_by_id(self, request: Request) -> Response:
        """Метод удаления записи из базы по id 

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """
        db_entity = await self.get_db_queries(request=request)
        params = await request.json()
        db_entity.delete_by_id(id=int(params.get('id')))
        return json_response(status=200, data={'message': 'Deleted'})    
    
    @route('PUT', '/')
    async def update(self, request: Request) -> Response:
        return Response(status=404, text='Error: Method not implement')
    
    @route('PUT', '/from_table')
    async def update_from_table(self, request: Request) -> Response:
        """Метод обновления данных записи в базе со страницы info

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """
        db_entity = await self.get_db_queries(request=request)
        params = await request.json()
        id = params.pop('id')
        db_entity.simple_update_by_id(id=id, to_update=params, merge_mode='replace')
        return json_response(status=200, data={'message': 'Updated'})
    
    @route('GET', '/all')
    async def get_all(self, request: Request) -> Response:
        """Метод получения всех записей по таблице из базы

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """
        sort_by = request.rel_url.query.get('sort[0][field]')
        direction = request.rel_url.query.get('sort[0][dir]')
        page = int(request.rel_url.query.get('page', 0))
        size = int(request.rel_url.query.get('size', 0))
        db_entity = await self.get_db_queries(request=request)
        res = db_entity.get_all(page=page, limit=size, sort_by=sort_by, direction=direction)
        res = [{k: v for k,v in i.items()} for i in res]
        total = db_entity.get_records_count()
        return json_response(status=200, data={'data': res, 'last_page': int(total / size) + 1})
    
    async def get_db_queries(self, request: Request) -> BaseQueries:
        """Метод получения объекта запросов к базу по сущности (self.queries_path)

        Args:
            request (Request): объект http запроса

        Returns:
            BaseQueries: объект запросов к базе
        """        
        db = await get_db_by_session(request=request)
        return db.__getattribute__(self.queries_path)