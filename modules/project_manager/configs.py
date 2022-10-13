import os
import json
from modules.project_manager.structure import Files, Folders, Variables, FilesNames
from exceptions.loggers import get_logger


class Configs:
    """Класс конфигураций проекта
    """    
    def __init__(self, project_path: str, project_name: str, iface: str=None):
        self.project_path = os.path.abspath(project_path)
        self.__generate_configs(project_name=project_name, iface=iface)
        self.logger = get_logger(self.__module__, handlers=[])
        
    def __generate_configs(self, project_name: str, iface: str) -> None:
        """Метод генерации конфигов класса
        """
        format_path =  os.path.join(self.project_path, '%s')
        self.folders = Folders(nmap_logs=format_path % FilesNames.nmap_logs,
                               scapy_logs=format_path % FilesNames.scapy_logs,
                               screenshots=format_path % FilesNames.screenshots)
        self.files = Files(database_file=format_path % FilesNames.database_file,
                           project_configs=format_path % FilesNames.config_file)
        self.variables = Variables(iface=iface, project_name=project_name)
        
    def create_config_file(self, config_file_name: str=FilesNames.config_file) -> bool:
        """Метод генерации конфиг файла в json формате

        Args:
            config_file_name (str): имя конфиг файла, по умолчанию project_configs.json.

        Returns:
            bool: Результат операции
        """
        configs = self.get_config_dict()
        json.dump(configs, open(os.path.join(self.project_path, config_file_name), 'w'), default=lambda x: x.__dict__, sort_keys=True, indent='\t', ensure_ascii=False)
        self.logger.debug('Created config file with name "%s"', config_file_name)
        return True
    
    def load_config_from_file(self):
        """Метод загрузки конфигов из файла в объект

        Returns:
            Configs: объект конфигов
        """        
        configs = json.load(open(os.path.join(self.project_path, FilesNames.config_file), 'r'))
        self.folders = Folders(**configs.get('folders'))
        self.files = Files(**configs.get('files'))
        self.variables = Variables(**configs.get('variables'))
        return self
        
    def get_config_dict(self) -> dict:
        """Метод получения кофигов в python-dict формате

        Returns:
            dict: конфиги в формате dict
        """        
        return {i.__class__.__name__.lower(): i._asdict() for i in [self.folders, self.files, self.variables]}