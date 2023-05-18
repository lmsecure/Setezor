from .project import Project
import os
from exceptions.loggers import get_logger
from typing import Dict
import json


class ProjectManager:
    '''
    Класс управления проектами
    '''
    # FixMe remake projects_path to variable from config
    def __init__(self): #, projects_folder_path: str):
        path_prefix = os.path.split(os.environ.get('APPIMAGE'))[0] if os.environ.get('APPIMAGE') else './'
        self.projects_path = os.path.abspath(os.path.join(path_prefix, './projects/'))
        if not os.path.exists(self.projects_path):
            os.mkdir(self.projects_path)
        self.logger = get_logger(self.__module__, handlers=[])
        self.projects: Dict[str, Project]  = {}
        
    def get_exist_projects_name(self):
        valid_projects = []
        for i in os.listdir(self.projects_path):
            if os.path.isdir(path:=os.path.join(self.projects_path, i)):
                is_checked, details = Project.check_project(path)
                if is_checked:
                    valid_projects.append(i)
                else:
                    self.logger.debug('Project "%s" have invalid params. See details "%s', i, details)
        self.logger.debug('Get %s valide projects', len(valid_projects))        
        return valid_projects
    
    def get_project(self, project_name: str) -> Project:
        if project:=self.projects.get(project_name):
            return project
        else:
            raise Exception('Project does not exists')
        
    def create_project(self, project_name: str, iface: str) -> Project:
        project = Project.create(name=project_name, path=self.projects_path, iface=iface)
        self.projects.update({project_name: project})
        self.logger.debug('Create project "%s"', project_name)
        return project
    
    def delete_project(self, project_name: str) -> None:
        if project_name in self.projects.keys():
            if _:=len(self.projects.get(project_name).clients):
                raise Exception(f'Can not delete project because it have {_} clients')
            self.projects.pop(project_name)
        Project.delete(path=self.projects_path, name=project_name)
    
    def load_project(self, project_name: str):
        project = None
        if project_name in self.projects.keys():
            self.logger.debug('Project "%s" already in project_manager', project_name)
            project = self.projects.get(project_name)
        else:
            project = Project.load(name=project_name, path=self.projects_path)
            self.projects.update({project_name: project})
            self.logger.debug('Load project "%s"', project_name)
        return project
    
    def add_client(self, uuid: str, project_name: str):
        project = self.projects.get(project_name)
        project.clients.create_client(uuid)
        project.observer.attach_many(project.clients.get_client_queues(uuid))
        self.logger.debug('Add client "%s" to project "%s"', uuid, project_name)
    
    def remove_client(self, project_name: str, uuid: str):
        project = self.projects.get(project_name)
        project.remove_client_from_observer(client_uuid=uuid)
        project.clients.delete_client(uuid=uuid)
        self.logger.debug('Remove client "%s" from project "%s"', uuid, project_name)
    
    def add_websocket_to_queue(self, project_name: str, uuid: str, queue_name: str, web_socket):
        project = self.projects.get(project_name)
        ws_queue = project.clients.get_queue(uuid=uuid, name=queue_name)
        ws_queue.websocket = web_socket
        self.logger.debug('Set websocket to queue "%s" to client "%s"', queue_name, uuid)
    
    def remove_ws_queue(self):
        pass
    
    def notify_clients(self, project_name: str, message: dict, queue_type: str):
        project = self.projects.get(project_name)
        project.observer.notify(message=message, queue_type=queue_type)
        self.logger.debug('Notify clients of project "%s" with message "%s"', project_name, json.dumps(message))

    def notify_single_client(self, project_name: str, message: dict, queue_type: str, client_uuid: str):
        queue = self.projects.get(project_name).clients.get_queue(name=queue_type, uuid=client_uuid)
        queue.put_item(message=message)
        self.logger.debug('Notify single client "%s" of project "%s" with message "%s"', 
                          client_uuid, project_name, message)
        
    def create_mock_project(self,):
        project = Project(name='*', path='', configs='', is_temp=True)
        self.projects.update({'*': project})
        