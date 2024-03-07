from dataclasses import dataclass
from typing import Dict, Type, TypeVar
from logging import Logger

T = TypeVar('T')

class BaseStruct:
    @classmethod
    def get_class_name(cls):
        return cls.__name__.lower()
    
    def __iter__(self):
        if hasattr(self, '__slots__'):
            for v in self.__slots__:
                yield v
        else:
            for v in self.__dict__.values():
                yield v

def unpack_from_json(structure: Type[T], json_data: dict, logger: Logger | None = None) -> T:
    
    """Распаковывает json, если указан логгер и в json\'не есть лишние данные, будет появляться warning"""
    
    name: str = structure.get_class_name()
    data: dict = json_data[name]
    args = {}
    init = structure.__init__.__annotations__
    for k, v in data.items():
        if init.get(k):
            args[k] = v
        else:
            if logger:
                logger.warning(f'Config contains extra data for structure {name}: key - {k}, value - {v}')
    return structure(**args)
    

@dataclass
class Folders(BaseStruct):
    nmap_logs: str
    scapy_logs: str
    screenshots: str
    masscan_logs: str


@dataclass
class Files(BaseStruct):
    database_file: str
    project_configs: str


@dataclass
class Variables(BaseStruct):
    project_name: str


@dataclass
class SchedulerParams:
    limit: int
    pending_limit: int
    close_timeout: float


class SchedulersParams(BaseStruct):
    def __init__(self):
        self.schedulers: Dict[str, SchedulerParams] = {}

    def add(self, name: str, limit: int, pending_limit: int, close_timeout: float):
        self.schedulers.update({name: SchedulerParams(limit=limit, pending_limit=pending_limit,
                                                close_timeout=close_timeout)})
    
    @classmethod
    def load(cls, schedulers: Dict[str, Dict]):
        sch = cls()
        for name, values in schedulers.items():
            sch.add(name=name, **values)
        return sch
    
    @property
    def __dict__(self):
        return {k: v.__dict__ for k, v in self.schedulers.items()}


class FilesNames:
    nmap_logs = 'nmap_logs'
    scapy_logs = 'scapy_logs'
    masscan_logs = 'masscan_logs'
    screenshots = 'screenshots'
    database_file = 'database.sqlite'
    config_file = 'project_configs.json'
    