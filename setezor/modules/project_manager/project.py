import os
import shutil
from pathlib import Path

from .files import FilesStructure
from .configs import Configs
from setezor.app_routes.custom_types import Clients, MessageObserver, WebSocketQueue
from setezor.exceptions.loggers import get_logger
from .schedulers import Schedulers
from setezor.database.db_connection import DBConnection
from setezor.database.queries import Queries
from .acunetix_manager import AcunetixManager
from setezor.network_structures import AgentStruct


class Project:

    clients: Clients
    observer: MessageObserver
    db: Queries
    schedulers: Schedulers
    configs: Configs
    acunetix_manager: AcunetixManager
    logger = get_logger(__module__, handlers=[])

    def __init__(self, name: str, path: str, configs: Configs, acunetix_manager: AcunetixManager, is_temp: bool = False):
        self.path: str = path
        self.name: str = name
        self.configs = configs
        self.clients = Clients()
        self.observer = MessageObserver()
        self.acunetix_manager = acunetix_manager
        # self.db = DBConnection(configs.files.database_file)
        if not is_temp:
            self.db = Queries(configs.files.database_file)
            self.schedulers = Schedulers(configs.schedulers)

    @classmethod
    def create(cls, name: str, path: str):
        """метод создания проекта

        Args:
            name (str): имя проекта
            iface (str): имя сетевого интерфейса с которым будем работать

        Returns:
            None
        """
        project_path = os.path.join(path, name)
        if os.path.exists(project_path):
            cls.logger.info(
                'Project with name "%s" by path "%s" already exists', name, project_path)
            # return to web-page message via Response
            raise Exception('Project with this name already exists')
        configs: Configs = Configs.generate_configs(
            project_path=path, project_name=name)
        files = FilesStructure(folders=configs.folders, files=configs.files)
        files.create_project_structure()
        configs.save_config_file()
        acunetix_manager = AcunetixManager.load_acunetix_apis(
            configs.files.acunetix_configs)
        cls.logger.debug('Created project "%s" with configs %s',
                         name, configs.get_config_dict())
        return cls(name=name, path=path, configs=configs,acunetix_manager=acunetix_manager)

    @classmethod
    def load(cls, path: str):
        configs = Configs.load_config_from_file(project_path=path)
        acunetix_manager = AcunetixManager.load_acunetix_apis(
            configs.files.acunetix_configs)
        # ToDo check project_structure
        return cls(name=configs.variables.project_id, path=path, configs=configs, acunetix_manager=acunetix_manager)

    @classmethod
    def load_for_import(cls, path: str):
        Configs.load_config_from_file_for_import(project_path=path)
        return cls.load(path=path)

    @staticmethod
    def check_project(name: str) -> bool:
        return True, 'All Right'

    def delete(self):
        """метод удаления проекта

        Args:
        """
        self.logger.debug('Start deleting project "%s"',
                          self.configs.variables.project_name)
        shutil.rmtree(self.configs.project_path)
        self.logger.debug('Project "%s" is deleted',
                          self.configs.variables.project_name)
        # todo?
        # stop tasks in schedulers
        # stop all websockets, clear and delete web_queues
        # close db_connection

    def remove_client_from_observer(self, client_uuid: str):
        client_queues = self.clients.get_client_queues(uuid=client_uuid)
        for queue in client_queues:
            self.observer.detach(queue)
        self.logger.debug(
            'Clear observer from client "%s" queues in project "%s"', client_uuid, self.name)

    def __repr__(self):
        vars = self.configs.variables
        return f"<Project name='{vars.project_name}', id='{vars.project_id}'>"
