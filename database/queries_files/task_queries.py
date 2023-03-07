from operator import or_
from sqlalchemy.orm.session import Session
from database.models import Task
from tasks.task_status import TaskStatus
import json
from datetime import datetime, timedelta
from sqlalchemy.sql import and_, or_
from .base_queries import BaseQueries
import pandas as pd


class TaskQueries(BaseQueries):
    """Класс запросов к таблице задач
    """
    
    model = Task
    
    @BaseQueries.session_provide
    def create(self, session: Session, status: str, params: dict, **kwargs):
        """Метод создания объекта задачи

        Args:
            session (Session): сессия коннекта к базе
            status (str): статус задачи
            params (dict): параметры запуска задачи

        Returns:
            _type_: объект задачи
        """        
        task_obj = self.model(status=status, params=json.dumps(params))
        session.add(task_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, {'status': status, 'params': params})
        return task_obj

    @BaseQueries.session_provide
    def set_pending_status(self, session: Session, index: int):
        """Метод установки статуса задачи "Выпоняется"

        Args:
            session (Session): сессия коннекта к базе
            index (int): идентификатор задачи
        """        
        self.update(session=session, expression=(self.model.__table__.c.get('id') == index,), to_update={'status': TaskStatus.pending, 'started': datetime.now()})
        
    @BaseQueries.session_provide
    def set_finished_status(self, session: Session, index: int):
        """Метод установки статуса задачи "Завершена"

        Args:
            session (Session): сессия коннекта к базе
            index (int): идентификатор задачи
        """        
        self.update(session=session, expression=(self.model.__table__.c.get('id') == index,), to_update={'status': TaskStatus.finished, 'finished': datetime.now()})
                
    @BaseQueries.session_provide    
    def set_failed_status(self, session: Session, index: int, error_message: str):
        """Метод установки статуса задачи "Завершена с ошибкой"

        Args:
            session (Session): сессия коннекта к базе
            index (int): идентификатор задачи
        """        
        self.update(session=session, expression=(self.model.__table__.c.get('id') == index,), to_update={'status': TaskStatus.failed, 'finished': datetime.now(), 'comment': error_message})
        
    @BaseQueries.session_provide
    def get_last_finished_tasks(self, session: Session, interval: int) -> pd.DataFrame:
        """Метод получения задач, завершенных в течение interval секунд

        Args:
            session (Session): сессия коннекта к базе
            interval (int): интервал в секундах, за который были завершены задачи

        Returns:
            pd.DataFrame: DataFrame последних завершенных задач
        """        
        last_time = datetime.now() - timedelta(seconds=interval)
        tasks = session.query(self.model).filter(self.model.finished > last_time, or_(self.model.status == TaskStatus.finished, self.model.status == TaskStatus.failed)).all()
        self.logger.debug('Found %s complited tasks in the last %s seconds', len(tasks), interval)
        return pd.DataFrame([i.to_dict() for i in tasks])

    @BaseQueries.session_provide
    def get_not_finished_tasks(self, session: Session) -> list:
        """Метод получения незавершенных задач

        Args:
            session (Session): сессия коннекта к базе

        Returns:
            list: массив незавершенных задач
        """        
        return [i.to_dict() for i in session.query(self.model).filter(and_(self.model.status != TaskStatus.finished, self.model.status != TaskStatus.failed)).all()]

    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},
                {'name': 'status', 'type': '', 'required': True},
                {'name': 'created', 'type': 'date', 'required': False},
                {'name': 'started', 'type': 'date', 'required': False},
                {'name': 'finished', 'type': 'date', 'required': False},
                {'name': 'params', 'type': '', 'required': False},
                {'name': 'comment', 'type': '', 'required': False},]
        
    @BaseQueries.session_provide
    def simple_create(self, session: Session, status: str, created: float=None, started: float=None, finished: float=None, params: str=None, comment: str=None):
        created = datetime.fromtimestamp(created) if created else None
        started = datetime.fromtimestamp(started) if started else None
        finished = datetime.fromtimestamp(finished) if finished else None
        task = self.model(status=status, created=created, started=started, finished=finished, params=params, comment=comment)
        session.add(task)
        session.flush()
