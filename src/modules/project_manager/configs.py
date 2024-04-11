from typing import Dict
import os
import json
import uuid

from .structure import (
    Files,
    Folders,
    Variables,
    FilesNames,
    SchedulersParams,
    unpack_from_json
)
from .exceptions import (
    FileNotExistsError,
    FileSaveError,
    ConfigLoadError
)
from exceptions.loggers import get_logger

class ConfigsFiller:
    
    def __init__(self,) -> None:
        self.is_config_changed = False
    
    def __call__(self, data: dict):
        self.is_config_changed = True
        return str(uuid.uuid4())
    
    def __save(self, configs: 'Configs'):
        configs.save_config_file()
    
    def save(self, configs: 'Configs'):
        
        '''Сохраняет конфиг, если были изменения'''
        
        if self.is_config_changed:
            self.__save(configs)

class Configs:
    """Класс конфигураций проекта
    """
    project_path: str
    files: Files
    folders: Folders
    variables: Variables
    schedulers: SchedulersParams
    logger = get_logger(__module__)
    # FixMe add schedulers
        
    def __init__(self, project_path: str, files: Files, folders: Folders,
                 variables: Variables, schedulers_params: SchedulersParams):
        self.project_path = os.path.abspath(project_path)
        self.files = files
        self.folders = folders
        self.variables = variables
        self.schedulers = schedulers_params
        
    @classmethod
    def generate_configs(cls, project_path:str, project_name: str):
        """Метод генерации конфигов класса
        """
        uid = str(uuid.uuid4())
        format_path =  os.path.join(project_path, uid, '%s')
        folders = Folders(nmap_logs=format_path % FilesNames.nmap_logs,
                          scapy_logs=format_path % FilesNames.scapy_logs,
                          screenshots=format_path % FilesNames.screenshots,
                          masscan_logs=format_path % FilesNames.masscan_logs)
        files = Files(database_file=format_path % FilesNames.database_file,
                      project_configs=format_path % FilesNames.config_file)
        variables = Variables(project_id=uid, project_name=project_name)
        schedulers_params = SchedulersParams.load({  # FixMe set input params to create schedulers params
            'scapy': {'limit': 1, 'pending_limit': 1, 'close_timeout': 0.1},
            'nmap': {'limit': 1, 'pending_limit': 10, 'close_timeout': 0.1},
            'masscan': {'limit': 1, 'pending_limit': 10, 'close_timeout': 0.1},
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
            with open(os.path.join(self.project_path, config_file_name), 'w') as f:
                json.dump(configs, f,
                        default=lambda x: x.__dict__, sort_keys=True, indent='\t', ensure_ascii=False)
        except Exception:
            raise FileSaveError('Cannot save config file')
    
    @classmethod
    def load_config_from_file(cls, project_path):
        """Метод загрузки конфигов из файла в объект

        Returns:
            Configs: объект конфигов
        """
        if not os.path.exists(file_path:=os.path.join(project_path, FilesNames.config_file)):
            raise FileNotExistsError(f'Config file dont exists by path "{file_path}"')
        with open(file_path, 'r') as f:
            configs_json: Dict[str, Dict[str, str]] = json.load(f)
        filler = ConfigsFiller()
        
        folders = unpack_from_json(Folders, configs_json, cls.logger)
        files = unpack_from_json(Files, configs_json, cls.logger)
        variables = unpack_from_json(Variables, configs_json, cls.logger, {'project_id': filler})
        schedulers_params = SchedulersParams.load(configs_json.get(SchedulersParams.get_class_name()))

        conf =  cls(project_path=project_path, files=files, folders=folders,
                   variables=variables, schedulers_params=schedulers_params)
        filler.save(conf)
        return conf
        
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