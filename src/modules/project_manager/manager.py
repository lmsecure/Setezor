import os
from typing import Dict
import json

from .project import Project, Configs
from .structure import Variables
from exceptions.loggers import get_logger
from .project_info import ProjectInfo, FrequentValue
from .storage import MemoryProjectStorage

class ProjectManager:
    '''
    Класс управления проектами
    '''
    # FixMe remake projects_path to variable from config
    def __init__(self): #, projects_folder_path: str):
        self.project_storage = MemoryProjectStorage()
        self.projects_path = self.project_storage.projects_path
        self.logger = get_logger(self.__module__, handlers=[])
        
    async def get_exist_projects_name(self):
        projects = [proj for proj in (i.configs.variables.project_name for i in await self.project_storage.get_projects()) if proj != '*']
        return projects
    
    async def get_project(self, project_id: str) -> Project:
        return await self.project_storage.get_project(project_id)
        
    async def create_project(self, project_name: str) -> Project:
        project = await self.project_storage.create_project(project_name)
        self.logger.debug('Create project "%s"', project_name)
        return project
    
    async def delete_project(self, project_id: str) -> None:
        await self.project_storage.delete_project(project_id)
    
    async def add_client(self, uuid: str, project_id: str):
        project = await self.project_storage.get_project(project_id)
        project.clients.create_client(uuid)
        project.observer.attach_many(project.clients.get_client_queues(uuid))
        self.logger.debug('Add client "%s" to project "%s"', uuid, project_id)
    
    async def remove_client(self, project_id: str, uuid: str):
        project = await self.project_storage.get_project(project_id)
        project.remove_client_from_observer(client_uuid=uuid)
        project.clients.delete_client(uuid=uuid)
        self.logger.debug('Remove client "%s" from project "%s"', uuid, project_id)
    
    async def add_websocket_to_queue(self, project_id: str, uuid: str, queue_name: str, web_socket):
        project = await self.project_storage.get_project(project_id)
        ws_queue = project.clients.get_queue(uuid=uuid, name=queue_name)
        ws_queue.websocket = web_socket
        self.logger.debug('Set websocket to queue "%s" to client "%s"', queue_name, uuid)
    
    def remove_ws_queue(self):
        pass
    
    async def notify_clients(self, project_id: str, message: dict, queue_type: str):
        project = await self.project_storage.get_project(project_id)
        project.observer.notify(message=message, queue_type=queue_type)
        self.logger.debug('Notify clients of project "%s" with message "%s"', project_id, json.dumps(message))

    async def notify_single_client(self, project_id: str, message: dict, queue_type: str, client_uuid: str):
        project = await self.project_storage.get_project(project_id)
        queue = project.clients.get_queue(name=queue_type, uuid=client_uuid)
        queue.put_item(message=message)
        self.logger.debug('Notify single client "%s" of project "%s" with message "%s"', 
                          client_uuid, project_id, message)


    async def create_mock_project(self,):
        conf = Configs('', '', '', Variables('*', '*'), '')
        project = Project(name='*', path='', configs=conf, is_temp=True)
        self.mock = project
        await self.project_storage.add_project(project)
        
    def get_project_info(self, project: Project, top_limit: int | None = 7):
        db = project.db
        top_object_types = [FrequentValue('object_type', i[1], i[0]) for i in 
                        db.object.get_most_frequent_values(column='object_type', 
                        limit=top_limit, except_values=[None])]
        top_protocols = [FrequentValue('protocol', i[1], i[0]) for i in
                        db.port.get_most_frequent_values(column='protocol', 
                        limit=top_limit, except_values=[None])]
        top_ports = [FrequentValue('port', i[1], i[0]) for i in
                        db.port.get_most_frequent_values(column='port', 
                        limit=top_limit, except_values=[None])]
        top_products = [FrequentValue('product', i[1], i[0]) for i in
                        db.port.get_most_frequent_values(column='product', 
                        limit=top_limit, except_values=[None])]
        stat = ProjectInfo(
            name=project.configs.variables.project_name,
            project_id=project.configs.variables.project_id,
            object_count=db.object.count(),
            ip_count=db.ip.count(except_values={'ip': [None, '']}),
            mac_count=db.mac.count(except_values={'mac': [None, '']}),
            l3_link_count=db.l3link.count(),
            port_count=db.port.count(except_values={'port': [None, '']}),
            
            top_object_type=top_object_types,
            top_ports=top_ports,
            top_protocols=top_protocols,
            top_products=top_products
        )
        return stat

    async def get_projects_info(self, top_limit: int | None = None):
        
        projects = (i for i in await self.project_storage.get_projects() if i.configs.variables.project_id != '*')
        stats: list[ProjectInfo] = []
        for project in projects:
            stat = self.get_project_info(project, top_limit=top_limit)
            stats.append(stat)
        return stats