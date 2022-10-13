from aiohttp.web import Request, Response, Application, json_response
from aiohttp_session import Session, get_session
from modules.project_manager.manager import ProjectManager
from database.queries import Queries
from routes.api.base_web_view import BaseView


class ProjectView(BaseView):
    endpoint = '/project'
    queries_path = 'project'
    
    async def create_from_table(self, request: Request) -> Response:
        pass
    
    @BaseView.route('POST', '/')
    async def create(self, request: Request) -> Response:
        """Метод создания проекта
        создает проект и привязывает идентификатор сессии к нему

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """        
        project_data = await request.json()
        project_manager = ProjectManager()
        status, message = project_manager.create_project(**project_data)
        if not status:
            return json_response(status=400, data={'status': False, 'message': message})
        session = await get_session(request)
        self.set_project_data_to_session(session=session, project_name=project_data.get('project_name'), app=request.app)
        return json_response(status=200, data={'status': True, 'data': message})
    
    @BaseView.route('DELETE', '/')
    async def delete_by_id(self, request: Request) -> Response:
        params = await request.post()
        project_name = params.get('project_name')
        session = await get_session(request)
        manager = ProjectManager()
        manager.delete_project(project_name=project_name)
        return json_response(status=200, data={'message': 'Project "%s" deleted' % project_name})
        
    
    async def update(self, request: Request) -> Response:
        pass
    
    async def get_all(self, request: Request) -> Response:
        pass

    @BaseView.route('GET', '/{name}')
    async def set_project(self, request: Request) -> Response:
        """Метод привязки идентификатора сессии к существующему проекту

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """        
        project_name = request.match_info.get('name')
        session = await get_session(request)
        # try:
        self.set_project_data_to_session(session=session, project_name=project_name , app=request.app)
        # except:
        #     raise Exception(f'Could not find project {project_name}')
        # ToDo add check project name in projects (by project manager) and set in session
        return json_response(status=200, data={'status': True, 'message': 'Setted'})

    def set_project_data_to_session(self, session: Session, project_name: str, app: Application) -> None:
        """Устанавливает в сессию конфиги проекта и создает в aiohttp сервере подключение к базе

        Args:
            session (Session): http сессия пользователя
            project_name (str): имя проекта
            app (Application): объект aiohttp сервера
        """        
        project_manager = ProjectManager()
        session['project_config'] = project_manager.get_project_config(project_name=project_name)
        session['project_name'] = project_name
        if not app['db'].get(project_name):
            app['db'][project_name] = Queries(session['project_config']['files'].get('database_file'))