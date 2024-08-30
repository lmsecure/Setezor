from typing import Dict
import os
import json
import uuid

import orjson
from pydantic import BaseModel

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
from setezor.tools.ip_tools import get_interfaces, get_default_interface
from setezor.exceptions.loggers import get_logger
from setezor.network_structures import AgentStruct

class ConfigsFiller:
    
    def __init__(self, function) -> None:
        """
        Заполнитель не достающих значений, принимает callable объект,
        который на вход принимает исходный словарь

        :param function: функция с 1 аргументом
        """
        self.is_config_changed = False
        self.function = function
    
    def __call__(self, data: dict):
        self.is_config_changed = True
        return self.function(data)
    
    def _save(self, configs: 'Configs'):
        configs.save_config_file()
    
    def save(self, configs: 'Configs'):
        
        '''Сохраняет конфиг, если были изменения'''
        
        if self.is_config_changed:
            self._save(configs)

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
                          masscan_logs=format_path % FilesNames.masscan_logs,
                          certificates_folder = format_path % FilesNames.certificates_folder)
        files = Files(database_file=format_path % FilesNames.database_file,
                      project_configs=format_path % FilesNames.config_file,
                      acunetix_configs=format_path % FilesNames.acunetix_configs)
        variables = Variables(project_id=uid, project_name=project_name, default_agent=AgentStruct(name='Default agent'))
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
            with open(os.path.join(self.project_path, config_file_name), 'wb') as f:
                data = orjson.dumps(configs,
                        default=lambda x: x.model_dump() if isinstance(x, BaseModel) else x.__dict__, option=orjson.OPT_INDENT_2)
                f.write(data)
        except Exception:
            raise FileSaveError('Cannot save config file')
    
    @classmethod
    def fill_interface(cls, data: dict):
        ifaces = get_interfaces()
        default = get_default_interface()
        default = next((i for i in ifaces if i.name == default))
        return default
    
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
        uid_filler = ConfigsFiller(lambda x: str(uuid.uuid4()))
        agent_filler = ConfigsFiller(lambda x: AgentStruct(name='Default agent'))
        interface_filler = ConfigsFiller(cls.fill_interface)
        
        folders = unpack_from_json(Folders, configs_json, cls.logger)
        files = unpack_from_json(Files, configs_json, cls.logger)
        variables = unpack_from_json(Variables, configs_json, cls.logger, 
                                     {'project_id': uid_filler, 
                                      'default_agent': agent_filler,
                                      'default_interface': interface_filler})
        schedulers_params = SchedulersParams.load(configs_json.get(SchedulersParams.get_class_name()))

        conf =  cls(project_path=project_path, files=files, folders=folders,
                   variables=variables, schedulers_params=schedulers_params)
        if any((uid_filler.is_config_changed, 
                agent_filler.is_config_changed, 
                interface_filler.is_config_changed)):
            uid_filler._save(conf)
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