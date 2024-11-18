from abc import ABC, abstractclassmethod
import os
import asyncio
from pathlib import Path
from typing import Any

from setezor.exceptions.loggers import get_logger
from .project import Project

class ProjectStorage(ABC):
    
    """Абстрактный класс хранилища проектов"""
    
    @abstractclassmethod
    async def get_projects(self) -> list[Project]:
        ...
    
    @abstractclassmethod
    async def get_project(self, id: Any) -> Project:
        ...
        
    @abstractclassmethod
    async def create_project(self, name: str) -> Project:
        ...
        
    @abstractclassmethod
    async def add_project(self, project: Project):
        ...
    
    @abstractclassmethod
    async def delete_project(self, id: Any):
        ...

    @abstractclassmethod
    async def rename_project(self, id: Any, new_name: str) -> Project:
        ...


class MemoryProjectStorage(ProjectStorage):
    
    """Хранилище словарь, все проекты загружаются при инициализации класса"""
    
    def __init__(self) -> None:
        self.projects: dict[str,Project] = {}
        path_prefix = os.path.split(os.environ.get('APPIMAGE'))[0] if os.environ.get('APPIMAGE') else os.path.join(os.path.expanduser('~'), '.local/share/setezor')
        self.projects_path = os.path.abspath(os.path.join(path_prefix, './projects/'))
        if not os.path.exists(self.projects_path):
            os.makedirs(self.projects_path, exist_ok=True)
        self.logger = get_logger(self.__module__, handlers=[])
        self.__load_projects()

    def __load_projects(self):
        folders = Path(self.projects_path).absolute().iterdir()
        for folder in folders:
            if not folder.is_dir():
                continue
            try:
                project = Project.load(str(folder))
                self.projects[project.configs.variables.project_id] = project
            except Exception:
                self.logger.error(f'Can not load config with path {folder}', exc_info=True)

    async def get_projects(self) -> list[Project]:
        return list(self.projects.values())

    async def get_project(self, id: str) -> Project:
        return self.projects[id]

    async def create_project(self, name: str) -> Project:
        # fixme asyncio.to_thread ломается
        project = Project.create(name, self.projects_path)
        self.projects[project.configs.variables.project_id] = project
        self.logger.debug('Create project "%s"', name)
        return project
    
    async def add_project(self, project: Project):
        self.projects[project.configs.variables.project_id] = project

    async def delete_project(self, id: str):
        project = self.projects[id]
        await asyncio.to_thread(project.delete)
        del self.projects[id]

    async def rename_project(self, id: str, new_name: str):
        project = self.projects[id]
        project.configs.variables.project_name = new_name
        await asyncio.to_thread(project.configs.save_config_file)
        return project
    
    def _load_new(self):
        
        # todo! нужно придумать способ подгрузки проектов из папки, или добавить метод в родительский класс
        """Метод, который подгрузит новые проекты из папки, 
        так не должно быть, нужно будет переделать"""
        
        folders = Path(self.projects_path).absolute().iterdir()
        exists = set((i.configs.project_path for i in self.projects.values()))
        for folder in folders:
            if str(folder) in exists:
                continue
            if not folder.is_dir():
                continue
            project = Project.load(str(folder))
            self.projects[project.configs.variables.project_id] = project


    def _load_new_for_import(self):
        
        # todo! нужно придумать способ подгрузки проектов из папки, или добавить метод в родительский класс
        """Метод, который подгрузит новые проекты из папки, 
        так не должно быть, нужно будет переделать"""
        
        folders = Path(self.projects_path).absolute().iterdir()
        exists = set((i.configs.project_path for i in self.projects.values()))
        for folder in folders:
            if str(folder) in exists:
                continue
            if not folder.is_dir():
                continue
            project = Project.load_for_import(str(folder))
            self.projects[project.configs.variables.project_id] = project