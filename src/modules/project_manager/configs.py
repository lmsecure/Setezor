import os
import json
from .structure import (
    Files,
    Folders,
    Variables,
    FilesNames,
    SchedulersParams
)
from .exceptions import (
    FileNotExistsError,
    FileSaveError,
    ConfigLoadError
)
from typing import Dict


class Configs:
    """Класс конфигураций проекта
    """
    project_path: str
    files: Files
    folders: Folders
    variables: Variables
    schedulers: SchedulersParams
    # FixMe add schedulers
        
    def __init__(self, project_path: str, files: Files, folders: Folders,
                 variables: Variables, schedulers_params: SchedulersParams):
        self.project_path = os.path.abspath(project_path)
        self.files = files
        self.folders = folders
        self.variables = variables
        self.schedulers = schedulers_params
        
    @classmethod
    def generate_configs(cls, project_path:str, project_name: str, iface: str):
        """Метод генерации конфигов класса
        """
        format_path =  os.path.join(project_path, project_name, '%s')
        folders = Folders(nmap_logs=format_path % FilesNames.nmap_logs,
                          scapy_logs=format_path % FilesNames.scapy_logs,
                          screenshots=format_path % FilesNames.screenshots)
        files = Files(database_file=format_path % FilesNames.database_file,
                      project_configs=format_path % FilesNames.config_file)
        variables = Variables(iface=iface, project_name=project_name)
        schedulers_params = SchedulersParams.load({  # FixMe set input params to create schedulers params
            'scapy': {'limit': 1, 'pending_limit': 1, 'close_timeout': 0.1},
            'nmap': {'limit': 1, 'pending_limit': 10, 'close_timeout': 0.1},
            'other': {'limit': 10, 'pending_limit': 500, 'close_timeout': 0.1},
        })
        return cls(project_path=format_path % '', files=files, folders=folders,
                   variables=variables, schedulers_params=schedulers_params)
        
    def save_config_file(self, config_file_name: str = FilesNames.config_file):
        """Метод генерации конфиг файла в json формате

        Args:
            config_file_name (str): имя конфиг файла, по умолчанию project_configs.json.

        """
        try:
            configs = self.get_config_dict()
            json.dump(configs, open(os.path.join(self.project_path, config_file_name), 'w'),
                      default=lambda x: x.__dict__, sort_keys=True, indent='\t', ensure_ascii=False)
        except:
            raise FileSaveError('Cannot save config file')
    
    @classmethod
    def load_config_from_file(cls, project_path):
        """Метод загрузки конфигов из файла в объект

        Returns:
            Configs: объект конфигов
        """
        if not os.path.exists(file_path:=os.path.join(project_path, FilesNames.config_file)):
            raise FileNotExistsError(f'Config file dont exists by path "{file_path}"')
        configs_json: Dict[str, Dict[str, str]] = json.load(open(file_path, 'r'))
        try:
            folders = Folders(**configs_json.get(Folders.get_class_name()))
            files = Files(**configs_json.get(Files.get_class_name()))
            variables = Variables(**configs_json.get(Variables.get_class_name()))
            schedulers_params = SchedulersParams.load(configs_json.get(SchedulersParams.get_class_name()))
        except:
            raise ConfigLoadError('Error in parse config file')
        return cls(project_path=project_path, files=files, folders=folders,
                   variables=variables, schedulers_params=schedulers_params)
        
    def get_config_dict(self) -> dict:
        """Метод получения кофигов в python-dict формате

        Returns:
            dict: конфиги в формате dict
        """
        try:
            return {i.get_class_name(): i.__dict__ 
                    for i in [self.folders, self.files, self.variables, self.schedulers]}
        except:
            raise 