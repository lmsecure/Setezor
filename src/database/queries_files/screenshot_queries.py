from sqlalchemy.orm.session import Session
from database.models import Task, Screenshot
from .base_queries import BaseQueries
from .task_queries import TaskQueries
from .port_queries import PortQueries


class ScreenshotQueries(BaseQueries):
    """Класс запросов к таблице скриншотов
    """
    model = Screenshot
    
    def __init__(self, task: TaskQueries, port: PortQueries, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            task (TaskQueries): объект запросов к таблице задач
            port (PortQueries): объект запросов к таблице портов
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.task = task
        self.port = port
        
    @BaseQueries.session_provide
    def create(self, session: Session, path: str, task_id: int, ip: str=None, port: int=None, domain: str=None):
        """Метод создания объекта скриншота

        Args:
            session (Session): сессия коннекта к базе
            path (str): путь относительно проекта по которому находится файл скриншота
            task_id (int): идентификатор задачи
            ip (str, optional): ip адрес, по которому был сделан скриншот. Defaults to None.
            port (int, optional): порт, по которому был сделан скриншот. Defaults to None.
            domain (str, optional): домен, по которому был сделан скриншот. Defaults to None.

        Returns:
            _type_: объект скриншота
        """        
        domain_obj = None
        port_obj = self.port.get_or_create(session=session, ip=ip, port=port)
        task_obj = session.query(self.task.model).filter(self.task.model.id == task_id).first()
        screenshot_obj = self.model(screenshot_path=path, task=task_obj.id, port=port_obj.id, domain=domain_obj)
        session.add(screenshot_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, {'path': path, 'task_id': task_id, 'ip': ip, 'port': port, 'domain': domain})
        return screenshot_obj

    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},
                {'name': 'port', 'type': '', 'required': False},
                {'name': 'screenshot_path', 'type': '', 'required': True},
                {'name': 'task', 'type': '', 'required': False},
                {'name': 'domain', 'type': '', 'required': False},]