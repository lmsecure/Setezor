from dataclasses import dataclass
from typing import Dict


class BaseStruct:
    @classmethod
    def get_class_name(cls):
        return cls.__name__.lower()
    
    def __iter__(self):
        for k, v in self.__dict__.items():
            yield v

@dataclass
class Folders(BaseStruct):
    nmap_logs: str
    scapy_logs: str
    screenshots: str


@dataclass
class Files(BaseStruct):
    database_file: str
    project_configs: str


@dataclass
class Variables(BaseStruct):
    iface: str
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
    screenshots = 'screenshots'
    database_file = 'database.sqlite'
    config_file = 'project_configs.json'
    