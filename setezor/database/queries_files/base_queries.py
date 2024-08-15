from typing import TypedDict, Literal, Any, TypeVar
from datetime import datetime
from abc import abstractmethod, ABC
from functools import wraps

import pandas as pd
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.query import Query
from sqlalchemy import func, Column, select, desc

from ..models import IP, BaseModel
try:
    from exceptions.loggers import LoggerNames, get_logger
except ImportError:
    from ...exceptions.loggers import LoggerNames, get_logger

T = TypeVar('T')

class Mock:
    def __getattribute__(self, item):
        return None
    
class QueryFilter(TypedDict):
    
    field: str
    type: Literal['=', '<', '<=', '>', '>=', 'like']
    value: str
    
    
class BaseQueries(ABC):
    """Базовый класс для запросов
    """
    model: IP
    
    def __init__(self, session_maker: Session):
        self.logger = get_logger(LoggerNames.db)
        self.session_maker = session_maker
        
    def session_provide(func):
        """Декоратор, который гарантированно создает или передает уже имеющуюся сессию для метода.
        По завершении коммитит изменения.
        накладывает некоторые ограничения - все аргументы функции нужно передовать именнованно

        """
        @wraps(func)
        def wrapped(self, *args, **kwargs):
            if kwargs.get('session') or any([i for i in args if isinstance(i, Session)]):
                res = func(self, *args, **kwargs)
            else:
                with self.session_maker() as session:
                    kwargs.update({'session': session})
                    res = func(self, *args, **kwargs)
                    session.commit()
            return res
        return wrapped
    
    @session_provide
    def write(self, session: Session, ret: str=None, to_update: bool=False, **kwargs) -> None | str:
        """Ищет такой же объект в базе, если не находит - создает.
        По завершении может вернуть какое-либо поле объекта

        Args:
            session (Session): сессия коннекта к базе
            ret (str, optional): поле которое нужно вернуть. По-умолчанию возвращает весь объект
            
        Returns:
            None or str: _description_
        """
        obj = self.get_or_create(session=session, to_update=to_update, **kwargs)
        # obj_args = [f'{i}={obj.__getattribute__(i)}' for i in self.get_headers() if obj.__getattribute__(i)]
        # self.logger.info('Add "%s" with args: %s', self.model.__name__, {", ".join(obj_args)})
        session.flush()
        if ret:
            return obj.__getattribute__(ret)
        return obj

    @session_provide
    def write_many(self, session: Session, data: list, to_update: bool=True):
        """Делает множественную запись объектов по такому же принципу
        Если объект несуществует - записываем, если существует - не делаем ничего

        Args:
            session (Session): сессия коннекта к базе
            data (list): массив данных
        """
        objects = (self.get_or_create(session=session, to_update=to_update, **item) for item in data)
        objects = [i for i in objects if i]
        self.logger.info('Add %s "%s"', len(objects), self.model.__name__)
        session.flush()
        
    @abstractmethod
    def create(self, session: Session, *args, **kwargs):
        """Абстрактный метод создания объекта

        Args:
            session (Session): сессия коннекта к базе
        """
        pass
    
    @session_provide
    def get_by_id(self, *, session: Session, id: int):
        obj = session.query(self.model).where(self.model.id == id).first()
        return obj
    
    @session_provide
    def get_or_create(self, session: Session, to_update: bool=False, **kwargs):
        """Получает объект из базы, если его не существует - создает

        Args:
            session (_type_): сессия коннекта к базе

        Returns:
            _type_: объект записи из базы
        """
        obj = session.query(self.model).filter(*[self.model.__table__.c.get(k) == v for k, v in kwargs.items() if v])
        if self.check_exists(session=session, query=obj):
            if to_update:
                # print("_____________________________________________",obj.first().id, kwargs)
                self.update_by_id(id=obj.first().id, to_update=kwargs)
                
            self.logger.debug('Get "%s" object with kwargs %s', self.model.__name__, kwargs)
            return obj.first()
        else:
            self.logger.debug('Create new "%s" object with kwargs %s', self.model.__name__, kwargs)
            return self.create(session=session, **kwargs)
        
    @session_provide
    def check_exists(self, session: Session, query: Query, log_not_exists=False):
        res = session.query(query.exists()).scalar()
        if not (log_not_exists and res):
            self.logger.debug('"%s" object not found', self.__class__.__name__)
        return res
    
    
    def _get_all(self, session: Session, source_query, columns: list[Column], result_format: str='dict', page: int=None, 
                limit: int=None, sort_by: str=None, direction: str=None, 
                filters: list[QueryFilter] = [], model: BaseModel | None = None) -> list[dict] | pd.DataFrame:
        for query_filter in filters:
            query_type = query_filter.get('type')
            query_field = query_filter.get('field')
            query_value = query_filter.get('value')
            
            column = (i for i in columns if i.name == query_field)
            column = next(column, None)
            if column is None:
                raise ValueError(f'No such column with name `{query_field}` in table {model.__name__ if model else source_query}')
            if all((query_type, query_field, query_value)):
                match query_type:
                    case '=':
                        source_query = source_query.where(column == query_value)
                    case '!=':
                        source_query = source_query.where(column != query_value)
                    case '<':
                        source_query = source_query.where(column < query_value)
                    case '<=':
                        source_query = source_query.where(column <= query_value)
                    case '>':
                        source_query = source_query.where(column > query_value)
                    case '>=':
                        source_query = source_query.where(column >= query_value)
                    case 'like':
                        source_query = source_query.where(column.like(query_value))
                    case _:
                        self.logger.warning(f'No such search type: "{query_type}", only excepted {QueryFilter.__annotations__.get("type").__dict__["__args__"]}')
            else:
                raise ValueError('Not on fields in filter, filters must contain `type, field, value`')

        if sort_by and direction:
            if self.is_field_foreign_key(session=session, field_name=sort_by):
                sorting_field, relationship = self.foreign_key_order(sort_by)
                source_query = source_query.join(relationship)
            else:
                sorting_field = model.__table__.c.get(sort_by)
            if direction == 'desc':
                sorting_field = sorting_field.desc()
            source_query = source_query.order_by(sorting_field)
        if limit:
            source_query = source_query.limit(limit)
        if page:
            source_query = source_query.offset(limit * (page - 1))
        source_query = source_query.all()
        self.logger.debug('Get %s "%s"', len(source_query),  {model.__name__ if model else source_query})
        if result_format == 'dict':
            res_list = [i.to_dict() for i in source_query]
            return res_list
        elif result_format == 'pandas':
            res_list = [i.to_dict() for i in source_query]
            return pd.DataFrame(res_list)
        else:
            return source_query
        
        
    @session_provide
    def get_all(self, session: Session, result_format: Literal['dict', 'pandas', None] = 'dict', page: int=None, 
                limit: int=None, sort_by: str=None, direction: str=None, 
                filters: list[QueryFilter] = []) -> list[dict] | pd.DataFrame:
        """Получает все записи из базы по текущей сущности

        Args:
            session (Session): сессия коннекта к базе
            result_format (str, optional): формат возвращаемых данных dict или pandas. по умолчанию dict

        Returns:
            dict or pd.DataFrame: _description_
        """
        model = self.model
        source_query = session.query(model)
        
        columns =model.__table__._columns._all_columns
        return self._get_all(session=session, source_query=source_query, 
                              columns=columns, result_format=result_format,
                              page=page, limit=limit, sort_by=sort_by,
                              direction=direction, filters=filters, 
                              model=self.model)
        
    def foreign_key_order(self, field_name: str):
        pass
        
    @session_provide
    def is_field_foreign_key(self, session: Session, field_name):
        table_foreign_keys = [i.get('constrained_columns')[0] for i in inspect(session.get_bind()).get_foreign_keys(self.model.__tablename__)]
        return field_name in table_foreign_keys
        
    @session_provide
    def delete_by_id(self, session: Session, id: int):
        """Удаляет запись по id 

        Args:
            session (Session): сессия коннекта к базе
            id (int): идентификатор записи
        """
        obj_query = session.query(self.model).filter(self.model.id == id)
        if not self.check_exists(session=session, query=obj_query, log_not_exists=True):
            return
        obj = obj_query.first()
        obj_args = [f'{i.get("name")}={obj.__getattribute__(i.get("name"))}' for i in self.get_headers() if obj.__getattribute__(i.get('name'))]
        self.logger.info('Delete %s with args: %s ', self.model.__name__, ", ".join(obj_args))
        id = session.delete(obj)
        session.flush()
    
    @abstractmethod
    def get_headers(self, *args, **kwargs) -> list:
        """Возвращает все название колонок из таблицы текущей сущности

        Returns:
            list: массив имен колонок
        """
        return self.model.__table__.columns.keys()
    
    @session_provide
    def update(self, session: Session, expression: tuple, to_update: dict):
        """Обновляет запись в базе

        Args:
            session (Session): сессия коннекта к базе
            expression (tuple): условие для фильтрации
            to_update (dict): словарь колонок и значений для обновления

        Returns:
            _type_: _description_
        """
        self.logger.debug('Start update "%s" by expression "%s"', self.model.__name__, [str(i) for i in expression])
        obj_query = session.query(self.model).filter(*expression)
        if not self.check_exists(session=session, query=obj_query, log_not_exists=True):
            return None
        obj = obj_query.update(to_update)
        self.logger.info('Update "%s" object with id "%s" to new data %s', self.model.__name__, ','.join([str(i.id) for i in obj_query.all()]), to_update)
        session.flush()
        return obj
    
    @session_provide
    def update_by_id(self, session: Session, *, id: int, to_update: dict, merge_mode='merge'):
        id = int(id)
        to_update = {k: v for k,v in to_update.items() if v}
        obj_query = session.query(self.model).filter(self.model.get_column(self.model, 'id') == id)
        if not self.check_exists(session=session, query=obj_query, log_not_exists=True):
            self.logger('Cannot update not exists object "%s" with id "%s"', self.model.__name__, id)
            return None
        obj = obj_query.first()
        new_to_update = {}
        for k, v in to_update.items():
            if any([foreign_key.parent.name == k for foreign_key in list(self.model.__table__.foreign_keys)]): # if field is foreign_key
                for foreign_key in list(self.model.__table__.foreign_keys):
                    if foreign_key.parent.name == k:
                        parent_queries = [i for i in [v1 for k1, v1 in self.__dict__.items() if isinstance(v1, self.__class__.__base__)] 
                                          if i.model.__tablename__ == foreign_key.column.table.name][0]  # search queries_class
                        fk_obj = parent_queries.get_or_create(session=session, **{k: v})  # search object in fk table, if not exists - create record
                        if v != fk_obj.id:
                            new_to_update.update({k: fk_obj.id})
            else:
                try:
                    if merge_mode == 'merge':
                        obj_attr = obj.__getattribute__(k)
                        if v:
                            if not obj_attr and v:
                                new_to_update.update({k: v})
                            elif obj_attr != v:
                                new_to_update.update({k: ','.join([obj_attr, v])})
                    else:
                        new_to_update.update({k: v})
                except Exception:
                    continue
        obj = obj_query.update(new_to_update)
        self.logger.info('Update "%s" object with id "%s" to new data %s', self.model.__name__, ','.join([str(i.id) for i in obj_query.all()]), new_to_update)
        session.flush()


    @session_provide
    def get_records_count(self, session: Session):
        return session.query(func.count(self.model.__table__.c.get('id'))).scalar()
    
    @session_provide
    def simple_create(self, session: Session, **kwargs):
        try:
            entity = self.model(**kwargs)
            session.add(entity)
            session.flush()
        except Exception:
            raise Exception('Cannot create "%s" entity with params: %s. Expected params %s ', self.__class__.__name__, kwargs, self.model.__table__.c.keys())
    
    @session_provide
    def simple_update_by_id(self, session: Session, id: int, to_update: dict, merge_mode='merge'):
        id = int(id)
        to_update = {k: datetime.fromtimestamp(v) if k in ['created', 'started', 'finished'] else v for k,v in to_update.items() if v}
        obj_query = session.query(self.model).filter(self.model.get_column(self.model, 'id') == id)
        if not self.check_exists(session=session, query=obj_query, log_not_exists=True):
            self.logger('Cannot update not exists object "%s" with id "%s"', self.model.__name__, id)
            return None
        obj = obj_query.update(to_update)  # noqa: F841
        self.logger.info('Update "%s" object with id "%s" to new data %s', self.model.__name__, ','.join([str(i.id) for i in obj_query.all()]), to_update)
        session.flush()
    
    @session_provide
    def count(self, session: Session, *, except_values: dict[str, list[Any]] = {}):
        
        """Считает количество сток, опционально принимает словарь исключений {колонка: список исключений}"""
        
        stm = select(func.count()).select_from(self.model)
        for key, list_value in except_values.items():
            if None in list_value:
                stm = stm.where(getattr(self.model, key) != None)  # noqa: E711
                list_value.remove(None)
            stm = stm.where(getattr(self.model, key).notin_(list_value))
        res = session.scalar(stm)
        return res
    
    @session_provide
    def get_most_frequent_values(self, *, session: Session, column: str, 
                                 limit: int | None = None, 
                                 except_values: list[Any] | None = None) -> list[tuple[int|Any]]:
        
        """Запрос на получение самых распространенных значений в колонке.add()
        
        Возвращает (значение, количество)
        """
        
        stm = select(func.count(self.model.id).label('qty'), getattr(self.model, column))
        if except_values:
            if None in except_values:
                except_values.remove(None)
                stm = stm.where(getattr(self.model, column) != None)  # noqa: E711
            stm = stm.where(getattr(self.model, column).notin_(except_values))
        stm = stm.group_by(getattr(self.model, column)).order_by(desc('qty'))
        if limit:
            stm = stm.limit(limit)
        from sqlalchemy.engine.result import ChunkedIteratorResult
        res: ChunkedIteratorResult = session.execute(stm)
        res = [i for i in res.iterator]
        return res
    
    
    # ! Api v2 (with pydantic)
    
    # @session_provide
    # def create_in_bd(self, session: Session, *, struct):
        
    #     """Создает объект структуры в бд"""
        
    #     raise NotImplementedError()
    
    # @session_provide
    # def fill_struct(self, session: Session, struct: T, depth: int = 0) -> T:
        
    #     """Заполняет структуры из бд c указанной глубиной"""
        
    #     raise NotImplementedError()