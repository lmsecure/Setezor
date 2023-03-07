import os
import shutil
from .files import FilesStructure
from .configs import Configs
from routes.custom_types import Clients, MessageObserver, WebSocketQueue
from exceptions.loggers import get_logger
from .schedulers import Schedulers
from database.db_connection import DBConnection
from database.queries import Queries


class Project:
    
    clients: Clients
    observer: MessageObserver
    db: DBConnection
    schedulers: Schedulers
    configs: Configs
    logger = get_logger(__module__, handlers=[])
    
    def __init__(self, name: str, path: str, configs: Configs, is_temp: bool = False):
        self.path: str = path
        self.name: str = name
        self.configs = configs
        self.clients = Clients()
        self.observer = MessageObserver()
        # self.db = DBConnection(configs.files.database_file)
        if not is_temp:
            self.db = Queries(configs.files.database_file)
            self.schedulers = Schedulers(configs.schedulers)

    @classmethod
    def create(cls, name: str, path: str, iface: str):
        """метод создания проекта

        Args:
            name (str): имя проекта
            iface (str): имя сетевого интерфейса с которым будем работать

        Returns:
            None
        """
        project_path = os.path.join(path, name)
        if os.path.exists(project_path):
            cls.logger.info('Project with name "%s" by path "%s" already exists', name, project_path)
            raise Exception('Project with this name already exists')  # return to web-page message via Response
        configs: Configs = Configs.generate_configs(project_path=path, project_name=name, iface=iface)
        files = FilesStructure(folders=configs.folders, files=configs.files)
        files.create_project_structure()
        configs.save_config_file()
        cls.logger.debug('Created project "%s" with configs %s', name, configs.get_config_dict())
        return cls(name=name, path=path, configs=configs)

    @classmethod
    def load(cls, name: str, path: str):
        project_path = os.path.join(path, name)
        configs: Configs = Configs.load_config_from_file(project_path=project_path)
        # ToDo check project_structure
        return cls(name=name, path=path, configs=configs)

    @staticmethod
    def check_project(name: str) -> bool:
        return True, 'All Right'
    
    @classmethod
    def delete(cls, path: str, name: str):
        """метод удаления проекта

        Args:
        """
        cls.logger.debug('Start deleting project "%s"', name)  # FixMe validate project_name, maybe path traversal
        shutil.rmtree(os.path.join(path, name))
        cls.logger.debug('Project "%s" is deleted', name)
        # stop tasks in schedulers
        # stop all websockets, clear and delete web_queues
        # close db_connection
        
    def remove_client_from_observer(self, client_uuid: str):
        client_queues = self.clients.get_client_queues(uuid=client_uuid)
        for queue in client_queues:
            self.observer.detach(queue)
        self.logger.debug('Clear observer from client "%s" queues in project "%s"', client_uuid, self.name)