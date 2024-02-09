import os
import asyncio
import zipfile
import io
from uuid import uuid4
import socket
import re
import base64

from aiohttp.web import Request, Response, Application, json_response, HTTPFound
from aiohttp_session import Session, get_session
from alembic.config import Config as AlembicConfig
from alembic.script.base import ScriptDirectory
from alembic.command import upgrade, stamp

from app_routes.api.base_web_view import BaseView
from modules.project_manager.manager import ProjectManager
from database.queries import Queries
from app_routes.custom_types import Clients, MessageObserver
from app_routes.session import notify_client, notify_clients_in_project
from modules.application import PMRequest

def zip_dir(path: str, zip_file: zipfile.ZipFile):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip_file.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))

def unzip(file: io.BytesIO, dir: str):
    with zipfile.ZipFile(file) as zip_ref:
        zip_ref.extractall(dir)

class ProjectView(BaseView):
    endpoint = '/project'
    queries_path = 'project'
    
    async def create_from_table(self, request: PMRequest) -> Response:
        pass
    
    @BaseView.route('POST', '/')
    async def create(self, request: PMRequest) -> Response:
        """Метод создания проекта
        создает проект и привязывает идентификатор сессии к нему

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """
        project_data = await request.json()
        project_name = project_data.get('project_name')
        project_manager: ProjectManager = request.app.pm
        session = await get_session(request=request)
        try:
            if re.search(r'[^\w\-\_\(\)\[\]\!\@\"\?\: ]', project_name) or len(project_name) < 2:
                raise Exception('Project name contains invalid symbols')
            project = project_manager.create_project(**project_data)
            await self.set_project_data_to_session(request=request, project_name=project_name)
            await notify_client(request=request, queue_type='message',
                          message={'title': f'Create project "{project_name}"', 'type': 'info',
                                   'text': f'Successful create project "{project_name}"'})
            self.migrate_db(str(project.db.db.engine.url), 'stamp', request.app.base_path)
        except Exception as e:
            await notify_client(request=request, queue_type='message',
                          message={'title': 'Project creation error', 'type': 'error',
                                   'text': f'Raise error in project creation.<br>Message: {str(e)}'})
            return json_response(status=400, data={'message': str(e)})
        else:
            return HTTPFound(location='/network/')
    
    @BaseView.route('DELETE', '/')
    async def delete_by_id(self, request: PMRequest) -> Response:
        params = await request.json()
        project_name = params.get('project_name')
        project_manager: ProjectManager = request.app.pm
        session = await get_session(request)
        try:
            await self.set_project_data_to_session(request=request, project_name='*')
            project_manager.delete_project(project_name=project_name)
        except Exception as e:
            await notify_client(request=request, queue_type='message',
                          message={'title': 'Deleting project error', 'type': 'error',
                                   'text': f'Cannot delete project "{project_name}".<br>Message error: {str(e)}'})
            return Response(status=200)
        # client could have not  a project, maybe create starting mock project
        await notify_client(request=request, queue_type='message',
                     message={'title': f'Delete project "{project_name}"', 'type': 'info',
                              'text': f'Project "{project_name}" is deleted'})
        return Response(status=200)

    async def update(self, request: PMRequest) -> Response:
        pass
    
    async def get_all(self, request: PMRequest) -> Response:
        pass
    
    @BaseView.route('GET', '/export_project')
    async def export_project(self, request: PMRequest):
        
        """Роут для экспорта проекта, в параметрах должен быть project_name"""        
        
        project_name = request.rel_url.query.get('project_name')
        project_manager: ProjectManager = request.app.pm
        projects = await asyncio.to_thread(project_manager.get_exist_projects_name)
        if project_name in projects:
            project = project_manager.load_project(project_name)
            path = project.configs.project_path
            io_file = io.BytesIO()
            with zipfile.ZipFile(io_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                await asyncio.to_thread(zip_dir, path, zipf)
            return Response(body=io_file.getvalue(), headers={
                'Content-Type': 'application/zip, application/octet-stream',
                'CONTENT-DISPOSITION': f'attachment;filename={project_name}.zip'
            })
        else:
            return json_response(status=404)
        
    @BaseView.route('POST', '/import_project')
    async def import_project(self, request: PMRequest):
        
        
        data = await request.content.read()
        data = data.split(b',')[1]
        data = base64.b64decode(data)
        io_file = io.BytesIO()
        io_file.write(data)
        path = request.app.pm.projects_path
        await asyncio.to_thread(unzip, io_file, path)
        return json_response(status=200)
    
    
    @BaseView.route('GET', '/{name}')
    async def set_project(self, request: PMRequest) -> Response:
        """Метод привязки идентификатора сессии к существующему проекту

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """        
        project_name = request.match_info.get('name')
        project_manager: ProjectManager = request.app.pm
        project = project_manager.load_project(project_name=project_name)
        client_uuid = await self.set_project_data_to_session(request=request, project_name=project_name)
        if project_name != '*':  # fixme костыль
            self.migrate_db(str(project.db.db.engine.url), 'upgrade', request.app.base_path)
        await notify_client(request=request, queue_type='message',
                      message={'title': f'Set project "{project_name}"', 'type': 'info',
                               'text': f'At now you work in project "{project_name}"'})
        return HTTPFound(location='/network/')
    
    @BaseView.route('GET', '/ifaces_list')
    async def get_ifaces_list(self, request: PMRequest):
        ifaces = [name for index, name in socket.if_nameindex()]
        return json_response(status=200, data={'ifaces': ifaces})

    def migrate_db(self, db_url: str, migrate_type: str, base_path: str):
        alembic_config = AlembicConfig()
        alembic_config.set_main_option('script_location', os.path.join(base_path, 'migration'))
        alembic_config.set_main_option('sqlalchemy.url', db_url)
        last_revision = ScriptDirectory.from_config(alembic_config).get_current_head()
        if migrate_type == 'upgrade':
            upgrade(alembic_config, last_revision)
        elif migrate_type == 'stamp':
            stamp(alembic_config, last_revision)
        
    async def set_project_data_to_session(self, request: PMRequest, project_name: str) -> str:
        """Устанавливает в сессию конфиги проекта и создает в aiohttp сервере подключение к базе

        Args:
            project_name (str): имя проекта
        """
        # ToDo implement like a transaction
        session = await get_session(request)
        project_manager: ProjectManager = request.app.pm
        user_uuid = str(uuid4())
        if not session.get('user_uuid'):
            session['user_uuid'] = user_uuid
        else:
            user_uuid = session.get('user_uuid')
        # Remove client from old project
        if old_project_name:=session.get('project_name'):
            project_manager.remove_client(project_name=old_project_name, uuid=user_uuid)
        session['project_name'] = project_name
        # set client to current project
        project_manager.add_client(uuid=user_uuid, project_name=project_name)
        return user_uuid
    
        