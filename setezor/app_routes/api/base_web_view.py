from abc import ABC
from typing import Literal

import orjson
from aiohttp.web import Response, json_response

from setezor.database.queries_files.base_queries import BaseQueries
from setezor.app_routes.session import get_db_by_session, notify_client, project_require
from setezor.modules.application import PMRequest

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
    
    def route(method: Literal['GET', 'POST', 'PUT', 'UPDATE', 'DELETE'], path: str):
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
    async def create_from_table(self, request: PMRequest) -> Response:
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
                                                      'text': f'Create "{self.queries_path.capitalize()}" with params {orjson.dumps(params, ensure_ascii=False).decode()}'})
        return json_response(status=200, data={'message': 'Added'})
    
    @route('POST', '/')
    async def create(self, request: PMRequest) -> Response:
        return Response(status=404, text='Error: Method not implement')
    
    @route('DELETE', '/')
    async def delete_by_id(self, request: PMRequest) -> Response:
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
    async def update(self, request: PMRequest) -> Response:
        return Response(status=404, text='Error: Method not implement')
    
    @route('PUT', '/from_table')
    async def update_from_table(self, request: PMRequest) -> Response:
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
    @project_require
    async def get_all(self, request: PMRequest) -> Response:
        """Метод получения всех записей по таблице из базы

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """
        query = request.rel_url.query
        params = query.get('params', {})
        if params:
            params: dict = orjson.loads(params)
        sort = params.get('sort') # todo сделать сортировку по нескольким полям
        if sort:
            sort_by = sort[0].get('field')
            direction = sort[0].get('dir')
        else:
            direction = None
            sort_by = None
        page = int(params.get('page', 1))
        size = int(params.get('size', 10))
        filters: list[dict] = params.get('filter', [])
        db_entity = await self.get_db_queries(request=request)
        res = db_entity.get_all(page=page, limit=size, sort_by=sort_by, direction=direction, filters=filters)
        
        res = [{k: v for k,v in i.items()} for i in res]
        res = orjson.dumps(res)
        return Response(body=res)
    
    async def get_db_queries(self, request: PMRequest) -> BaseQueries:
        """Метод получения объекта запросов к базу по сущности (self.queries_path)

        Args:
            request (Request): объект http запроса

        Returns:
            BaseQueries: объект запросов к базе
        """        
        db = await get_db_by_session(request=request)
        return db.__getattribute__(self.queries_path)