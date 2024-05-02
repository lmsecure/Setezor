import os
import json
from typing import Literal

from alembic.config import Config as AlembicConfig
from alembic.script.base import ScriptDirectory
from alembic.command import upgrade, stamp

from .project import Project, Configs
from .structure import Variables
from exceptions.loggers import get_logger
from .project_info import ProjectInfo, FrequentValue
from .storage import MemoryProjectStorage

from tools.ip_tools import get_interfaces, get_default_interface
from network_structures import AgentStruct

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
        conf = Configs('', '', '', Variables('*', '*', '*'), '')
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
    
    
    async def setup(self):
        """
        Метод для инициализации менеджера, нужен, чтобы синхронизировать конфиги и бд
        """
        
        ifaces = get_interfaces()
        default_system_iface = next((i for i in ifaces if i.name == get_default_interface()), None)
        base_path = '/'.join(__file__.split('/')[:-3])
        for project in await self.project_storage.get_projects():
            self.migrate_db(str(project.db.db.engine.url), 'upgrade', base_path)            
            changed = False
            default_iface = project.configs.variables.default_interface
            default_agent = project.configs.variables.default_agent
            if default_iface not in [i.model_dump() for i in ifaces]:
                changed = True
                project.configs.variables.default_interface = default_system_iface.model_dump()
            
            if default_agent['id'] is None:
                changed = True
                agents = project.db.agent.get_all()
                default = next((i for i in agents if i.get('name') == 'Default agent'), None)
                if default:
                    project.configs.variables.default_agent['id'] = default['id']
                else:
                    db_agent = project.db.agent.create(agent=AgentStruct.model_validate(default_agent))
                    project.configs.variables.default_agent = AgentStruct.model_validate(db_agent, from_attributes=True).model_dump()
            if changed:
                project.configs.save_config_file()
                
    def migrate_db(self, db_url: str, migrate_type: Literal['upgrade', 'stamp'], base_path: str):
        alembic_config = AlembicConfig()
        alembic_config.set_main_option('script_location', os.path.join(base_path, 'migration'))
        alembic_config.set_main_option('sqlalchemy.url', db_url)
        last_revision = ScriptDirectory.from_config(alembic_config).get_current_head()
        if migrate_type == 'upgrade':
            upgrade(alembic_config, last_revision)
        elif migrate_type == 'stamp':
            stamp(alembic_config, last_revision)