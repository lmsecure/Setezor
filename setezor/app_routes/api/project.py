import os
import asyncio
import zipfile
import io
from uuid import uuid4
import re
from pathlib import Path
import base64
import magic
from aiohttp.web import Response, json_response, HTTPFound
from aiohttp_session import get_session

from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.project_manager.manager import ProjectManager
from setezor.app_routes.session import notify_client, project_require, get_db_by_session
from setezor.modules.application import PMRequest
from setezor.tools.ip_tools import get_interfaces, get_default_interface
from setezor.network_structures import IPv4Struct

def zip_dir(foldername: str, file: io.BytesIO, includeEmptyDIr=True):   
    empty_dirs = []  
    with zipfile.ZipFile(file, 'w', zipfile.ZIP_DEFLATED) as zip:
        main_dir_lenght = len(str(Path(foldername).parent))
        for root, dirs, files in os.walk(foldername):
            empty_dirs.extend([dir for dir in dirs if os.listdir(os.path.join(root, dir)) == []])  
            for name in files:
                zip.write(os.path.join(root ,name), os.path.join(root[main_dir_lenght:], name))  
            if includeEmptyDIr:
                root = root[main_dir_lenght:]
                for dir in empty_dirs:  
                    zif = zipfile.ZipInfo(os.path.join(root, dir) + "/")  
                    zip.writestr(zif, "")  
            empty_dirs = []  

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
        await get_session(request=request)
        try:
            if re.search(r'[^\w\-\_\(\)\[\]\!\@\"\?\: ]', project_name) or len(project_name) < 2:
                raise Exception('Project name contains invalid symbols')
            project = await project_manager.create_project(project_data['project_name'])
            await self.set_project_data_to_session(request=request, project_id=project.configs.variables.project_id)
            await notify_client(request=request, queue_type='message',
                          message={'title': f'Create project "{project_name}"', 'type': 'info',
                                   'text': f'Successful create project "{project_name}"'})
            project_manager.migrate_db(str(project.db.db.engine.url), 'stamp', request.app.base_path)
            db = await get_db_by_session(request)
            ifaces = get_interfaces()
            default_system_iface = next((i for i in ifaces if i.name == get_default_interface()), None)
            project.configs.variables.default_agent.ip = default_system_iface.ip_address
            db.ip.create(ip=project.configs.variables.default_agent.ip)
            db_agent = db.agent.create(agent=project.configs.variables.default_agent)
            project.configs.variables.default_interface = default_system_iface.model_dump()
            project.configs.variables.default_agent.id = db_agent.id
            project.configs.variables.search_vulns_token = ""
            project.configs.variables.default_agent = project.configs.variables.default_agent.model_dump()
            project.configs.save_config_file()
        except Exception as e:
            await notify_client(request=request, queue_type='message',
                          message={'title': 'Project creation error', 'type': 'error',
                                   'text': f'Raise error in project creation.<br>Message: {str(e)}'})
            return json_response(status=400, data={'message': str(e)})
        else:
            return HTTPFound(location='/projects_dashboard/')
    
    @BaseView.route('DELETE', '/')
    async def delete_by_id(self, request: PMRequest) -> Response:
        
        params = await request.json()
        project_id = params.get('project_id')
        project_manager: ProjectManager = request.app.pm
        
        await get_session(request)
        try:
            await self.set_project_data_to_session(request=request, project_id='*')
            await project_manager.delete_project(project_id=project_id)
        except Exception as e:
            await notify_client(request=request, queue_type='message',
                          message={'title': 'Deleting project error', 'type': 'error',
                                   'text': f'Cannot delete project "{project_id}".<br>Message error: {str(e)}'})
            return Response(status=200)
        # client could have not  a project, maybe create starting mock project
        await notify_client(request=request, queue_type='message',
                     message={'title': f'Delete project "{project_id}"', 'type': 'info',
                              'text': f'Project "{project_id}" is deleted'})
        return Response(status=200)

    async def update(self, request: PMRequest) -> Response:
        pass
    
    async def get_all(self, request: PMRequest) -> Response:
        pass
    
    
    @BaseView.route('GET', '/export_project')
    @project_require
    async def export_project(self, request: PMRequest):
        
        """Роут для экспорта проекта, в параметрах должен быть project_name"""        
        
        project_id = request.rel_url.query.get('project_id')
        project_manager: ProjectManager = request.app.pm
        try:
            project = await project_manager.get_project(project_id)
            path = project.configs.project_path
            io_file = io.BytesIO()
            await asyncio.to_thread(zip_dir, path, io_file)
            return Response(body=io_file.getvalue(), headers={
                'Content-Type': 'application/zip, application/octet-stream',
                'CONTENT-DISPOSITION': f'attachment;filename={ project.configs.variables.project_name}.zip'
            })
        except KeyError:
            return json_response(status=404, text='No such project')
        
    @BaseView.route('POST', '/import_project')
    async def import_project(self, request: PMRequest):
        
        
        data = await request.content.read()
        data = data.split(b',')[1]
        data = base64.b64decode(data)
        if len(data) == 0:
            await notify_client(request=request, queue_type='message',
                                message={'title': 'Error', 'type': 'error',
                                            'text': 'File empty'})            
            return Response(status=400)
        if magic.from_buffer(data)[:3] != "Zip":
            await notify_client(request=request, queue_type='message',
                                message={'title': 'Error', 'type': 'error',
                                            'text': 'Invalid file type'})      
            return Response(status=400)
        io_file = io.BytesIO()
        io_file.write(data)
        path = request.app.pm.projects_path
        await asyncio.to_thread(unzip, io_file, path)
        request.app.pm.project_storage._load_new_for_import() # todo переделать
        return json_response(status=200)
    
    
    @BaseView.route('GET', '/{project_id}')
    async def set_project(self, request: PMRequest) -> Response:
        """Метод привязки идентификатора сессии к существующему проекту

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """        
        project_id = request.match_info.get('project_id')
        project_manager: ProjectManager = request.app.pm
        project = await project_manager.project_storage.get_project(project_id)
        await self.set_project_data_to_session(request=request, project_id=project_id)
        if project_id != '*':  #! fixme костыль
            project_manager.migrate_db(str(project.db.db.engine.url), 'upgrade', request.app.base_path)
        await notify_client(request=request, queue_type='message',
                      message={'title': f'Set project "{project_id}"', 'type': 'info',
                               'text': f'At now you work in project "{project_id}"'})
        return HTTPFound(location='/projects_dashboard/')
    
    @BaseView.route('GET', '/ifaces_list')
    async def get_ifaces_list(self, request: PMRequest):
        
        """Возвращает список интерфейсов, у которых есть ipv4 адрес"""
        
        ifaces = [iface for iface in get_interfaces() if iface.ip_address]
        return json_response(status=200, data={'ifaces': ifaces})

        
    async def set_project_data_to_session(self, request: PMRequest, project_id: str) -> str:
        """Устанавливает в сессию конфиги проекта и создает в aiohttp сервере подключение к базе

        Args:
            project_name (str): имя проекта
        """
        # ToDo implement like a transaction
        session = await get_session(request)
        project_manager: ProjectManager = request.app.pm
        if not session.get('user_uuid'):
            user_uuid = str(uuid4())
            session['user_uuid'] = str(uuid4())
        else:
            user_uuid = session.get('user_uuid')
        # Remove client from old project
        if old_project_id:=session.get('project_id'):
            await project_manager.remove_client(project_id=old_project_id, uuid=user_uuid)
        session['project_id'] = project_id
        # set client to current project
        await project_manager.add_client(uuid=user_uuid, project_id=project_id)
        return user_uuid
    
    @BaseView.route('GET', '/get_projects_info')
    async def get_projects_info(self, request: PMRequest):
        
        res = request.app.pm.get_projects_info()
        return Response()
    
    
    @BaseView.route('PUT', '/rename_project')
    async def rename_project(self, request: PMRequest):
        
        request.get
        params = request.json()
        project_id = params['project_id']
        new_name = params['new_name']
        project = await request.app.pm.get_project(project_id)
        project.configs.variables.project_name = new_name
        project.configs.save_config_file()