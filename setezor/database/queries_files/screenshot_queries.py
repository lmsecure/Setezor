from sqlalchemy.orm.session import Session
from ..models import Task, Screenshot
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
    def create(self, session: Session,**kwargs):
        new_screenshot = self.model(**kwargs)
        session.add(new_screenshot)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s',
                          self.model.__name__, {'data': kwargs})
        return new_screenshot

    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},
                {'name': 'port', 'type': '', 'required': False},
                {'name': 'screenshot_path', 'type': '', 'required': True},
                {'name': 'task', 'type': '', 'required': False},
                {'name': 'domain', 'type': '', 'required': False},]