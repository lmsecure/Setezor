from modules.project_manager.files import FilesStructure
from modules.project_manager.configs import Configs
import os
from exceptions.loggers import get_logger
import traceback
import shutil


class ProjectManager:
    '''
    Класс управления проектами
    '''
    # FixMe remake projects_path to variable from config
    def __init__(self): #, projects_folder_path: str):
        self.projects_path = os.path.abspath('./projects/')
        if not os.path.exists(self.projects_path):
            os.mkdir(self.projects_path)
        self.logger = get_logger(self.__module__, handlers=[])
        
    def get_existing_projects_name(self):
        res = []
        for i in os.listdir(self.projects_path):
            if os.path.isdir(os.path.join(self.projects_path,i)):
                details = None
                try:
                    configs = Configs(os.path.join(self.projects_path, i), '').load_config_from_file()
                    f = FilesStructure(configs.folders._asdict(), configs.files._asdict())
                    check_status, details = f.check_project_structure()
                    if check_status:
                        res.append(i)
                except Exception as e:
                    self.logger.debug('In project "%s" get error: %s', i, e)
                    continue
        self.logger.debug('Get %s valide projects', len(res))        
        return res
    
    def create_project(self, project_name: str, iface: str) -> None:
        """метод создания проекта

        Args:
            project_name (str): имя проекта
            iface (str): имя сетевого интерфейса с которым будем работать

        Returns:
            None
        """
        project_path = os.path.join(self.projects_path, project_name)
        if os.path.exists(project_path):
            self.logger.info('Project with name "%s" by path "%s" already exists', project_name, project_path)
            return False, 'Project with this name already exists'
        config = Configs(project_path=project_path, project_name=project_name, iface=iface)
        files = FilesStructure(folders=config.folders._asdict(), files=config.files._asdict())
        files.create_project_structure()
        config.create_config_file()
        self.logger.debug('Created project "%s" with configs %s', project_name, config.get_config_dict())
        return True, 'Created'
    
    def delete_project(self, project_name: str) -> None:
        """метод удаления проекта

        Args:
            project_name (str): имя проекта

        """
        self.logger.debug('Start deleting project "%s"', project_name)  # FixMe validate project_name, maybe path traversal
        shutil.rmtree(os.path.join(self.projects_path, project_name))
        self.logger.debug('Project "%s" deleted', project_name)
    
    def get_project_config(self, project_name: str) -> Configs:
        """метод получения конфигов проекта

        Args:
            project_name (str): имя проекта

        Returns:
            Configs: класс конфигов проекта
        """        
        return Configs(os.path.join(self.projects_path, project_name), project_name=project_name).load_config_from_file().get_config_dict()