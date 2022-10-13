import json
from aiohttp.web import Request, Response, json_response
from routes.session import project_require, get_db_by_session, get_configs_by_session
from tasks.nmap_logs_task import NmapLogTask
from tasks.nmap_scan_task import NmapScanTask
from tasks.scapy_scan_task import ScapyScanTask
from tasks.scapy_logs_task import ScapyLogTask
from tasks.screenshot_task import ScreenshotTask
# from aiojobs.aiohttp import spawn
from aiojobs._scheduler import Scheduler
from tasks.task_status import TaskStatus
from routes.api.base_web_view import BaseView
import json


class TaskView(BaseView):
    endpoint = '/task'
    queries_path = 'task'

    tasks = {'nmap_log': NmapLogTask,
            'nmap_scan': NmapScanTask,
            'scapy_scan': ScapyScanTask,
            'scapy_log': ScapyLogTask,
            'screenshot': ScreenshotTask}
    
    @BaseView.route('POST', '/')
    @project_require
    async def create(self, request: Request) -> Response:
        """Метод создания задачи

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """        
        data = await request.json()
        task_type = data.get('task_type')
        scheduler: Scheduler = None
        task = TaskView.tasks.get(task_type)
        kwargs = data.get('args')
        db = await get_db_by_session(request=request)
        project_configs = await get_configs_by_session(request=request)
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(kwargs.get('to_log')), ret='id')
        if task_type.split('_')[1] == 'scan':
            scheduler = request.app['schedulers'].get(task_type.split('_')[0])
        else:
            scheduler = request.app['schedulers'].get('other')
        # ToDo check required args
        await scheduler.spawn(task().execute(db=db, task_id=task_id, iface=project_configs.get('variables').get('iface'), **project_configs.get('folders'), **kwargs))
        return json_response(status=200, data={'status': True, 'data': 'ok'})
    
    @BaseView.route('GET', '/all')
    @project_require
    async def get_all(self, request: Request) -> Response:
        """Метод получения всех записей по таблице из базы

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """
        sort_by = request.rel_url.query.get('sortBy')
        direction = request.rel_url.query.get('direction')
        page = int(request.rel_url.query.get('page'))
        limit = int(request.rel_url.query.get('limit'))
        task = await self.get_db_queries(request)
        data = task.get_all(result_format='pandas', page=page, limit=limit, sort_by=sort_by, direction=direction)
        data = data.astype(str).to_dict('records')
        return json_response(status=200, data={'records': data, 'total': task.get_records_count()})

    @BaseView.route('GET', '/last_finished')
    @project_require
    async def get_last_finished(self, request: Request) -> Response:
        """Метод получения завершенных задач за последние 5 секунд

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """        
        task = await self.get_db_queries(request)
        tasks = task.get_last_finished_tasks(interval=5)
        tasks = tasks.astype(str)
        return json_response(status=200, data={'status': True, 'data': tasks.to_dict('records')})
