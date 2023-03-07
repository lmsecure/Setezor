from sqlalchemy.orm.session import Session
from sqlalchemy.orm.query import Query
from sqlalchemy import func
from exceptions.loggers import LoggerNames, get_logger
from sqlalchemy.exc import OperationalError
from abc import abstractmethod, ABC
from database.models import IP
import pandas as pd
from functools import wraps
from sqlalchemy.inspection import inspect
from datetime import datetime

class Mock:
    def __getattribute__(self, item):
        return None
    
    
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
            if kwargs.get('session'):
                res = func(self, *args, **kwargs)
            else:
                with self.session_maker() as session:
                    kwargs.update({'session': session})
                    res = func(self, *args, **kwargs)
                    session.commit()
            return res
        return wrapped
    
    @session_provide
    def write(self, session: Session, ret: str=None, to_update: bool=False, **kwargs) -> None or str:
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
        objects = [self.get_or_create(session=session, to_update=to_update, **item) for item in data]
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
        
    @session_provide
    def get_all(self, session: Session, result_format: str='dict', page: int=None, limit: int=None, sort_by: str=None, direction: str=None) -> dict or pd.DataFrame:
        """Получает все записи из базы по текущей сущности

        Args:
            session (Session): сессия коннекта к базе
            result_format (str, optional): формат возвращаемых данных dict или pandas. по умолчанию dict

        Returns:
            dict or pd.DataFrame: _description_
        """
        source_query = session.query(self.model)
        if sort_by and direction:
            if self.is_field_foreign_key(session=session, field_name=sort_by):
                sorting_field, relationship = self.foreign_key_order(sort_by)
                source_query = source_query.join(relationship)
            else:
                sorting_field = self.model.__table__.c.get(sort_by)
            if direction == 'desc':
                sorting_field = sorting_field.desc()
            source_query = source_query.order_by(sorting_field)
        if limit:
            source_query = source_query.limit(limit)
        if page:
            source_query = source_query.offset(limit * (page - 1))
        source_query = source_query.all()
        self.logger.debug('Get %s "%s"', len(source_query), self.model.__name__)
        res_list = [i.to_dict() for i in source_query]
        if result_format == 'dict':
            return res_list
        elif result_format == 'pandas':
            return pd.DataFrame(res_list)
        else:
            return source_query
        
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
    def update_by_id(self, session: Session, id: int, to_update: dict, merge_mode='merge'):
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
                except:
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
        except:
            raise Exception('Cannot create "%s" entity with params: %s. Expected params %s ', self.__class__.__name__, kwargs, self.model.__table__.c.keys())
    
    @session_provide
    def simple_update_by_id(self, session: Session, id: int, to_update: dict, merge_mode='merge'):
        id = int(id)
        to_update = {k: datetime.fromtimestamp(v) if k in ['created', 'started', 'finished'] else v for k,v in to_update.items() if v}
        obj_query = session.query(self.model).filter(self.model.get_column(self.model, 'id') == id)
        if not self.check_exists(session=session, query=obj_query, log_not_exists=True):
            self.logger('Cannot update not exists object "%s" with id "%s"', self.model.__name__, id)
            return None
        obj = obj_query.update(to_update)
        self.logger.info('Update "%s" object with id "%s" to new data %s', self.model.__name__, ','.join([str(i.id) for i in obj_query.all()]), to_update)
        session.flush()