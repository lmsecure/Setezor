
from database import queries_files as qf
from database.db_connection import DBConnection


class Queries:
    """Класс управления запросами к базе
    """
    def __init__(self, db_path: str):
        """Инициализация объекта управления запросам
        хранит в себе запросы  в иерархичном виде

        Args:
            db_path (str): путь до базы
        """
        self.db = DBConnection(db_path)
        self.object = qf.ObjectQueries(session_maker=self.db.create_session())
        self.object_types = qf.ObjectTypeQueries(session_maker=self.db.create_session())
        self.mac = qf.MACQueries(objects=self.object, session_maker=self.db.create_session())
        self.ip = qf.IPQueries(mac=self.mac, session_maker=self.db.create_session())
        self.l3link = qf.L3LinkQueries(ip=self.ip, session_maker=self.db.create_session())
        self.port = qf.PortQueries(ip=self.ip, session_maker=self.db.create_session())
        self.task = qf.TaskQueries(session_maker=self.db.create_session())
        self.screenshot = qf.ScreenshotQueries(task=self.task, port=self.port, session_maker=self.db.create_session())