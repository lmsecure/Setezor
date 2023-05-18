from aiohttp.web import Request, Response, json_response
from routes.session import project_require, get_project, notify_client, notify_clients_in_project, get_db_by_session
from tasks.nmap_logs_task import NmapLogTask
from tasks.nmap_scan_task import NmapScanTask
from tasks.scapy_scan_task import ScapyScanTask
from tasks.scapy_logs_task import ScapyLogTask
from tasks.screenshot_by_ip_task import ScreenshotFromIPTask
from tasks.task_status import TaskStatus
from routes.api.base_web_view import BaseView
import json
from modules.project_manager.manager import ProjectManager
from datetime import datetime
from base64 import b64decode


class TaskView(BaseView):
    endpoint = '/task'
    queries_path = 'task'

    @BaseView.route('POST', '/nmap_scan')
    @project_require
    async def create_nmap_scan(self, request: Request):
        params = await request.json()
        project = await get_project(request=request)
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        scheduler = project.schedulers.get('nmap')
        await scheduler.spawn_job(NmapScanTask(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}',
                                               command=' '.join(params.values()), iface=project.configs.variables.iface,
                                               db = db, nmap_logs=project.configs.folders.nmap_logs, task_id=task_id))
        return Response(status=201)
    
    @BaseView.route('POST', '/nmap_log')
    @project_require
    async def create_nmap_log(self, request: Request):
        params = await request.json()
        log_file = params.pop('log_file')
        data = b64decode(log_file.split(',')[1])
        project = await get_project(request=request)
        scheduler = project.schedulers.get('other')
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        await scheduler.spawn_job(NmapLogTask(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}',
                                              data=data, iface=project.configs.variables.iface,
                                              db=db, nmap_logs=project.configs.folders.nmap_logs, task_id=task_id))
        return Response(status=201)
        
    @BaseView.route('POST', '/scapy_scan')
    @project_require
    async def create_scapy_scan(self, request: Request):
        project = await get_project(request=request)
        scheduler = project.schedulers.get('scapy')
        if scheduler.active_count >= scheduler.limit:
            await notify_client(request=request, queue_type='message',
                                message={'title': f'Task alredy running', 'type': 'warning',
                                         'text': f'Scanning by scapy already running'})
            return json_response(status=409, data={'message': 'Scanning by scapy already running'})
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params='', ret='id')
        await scheduler.spawn_job(ScapyScanTask(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}',
                                                iface=project.configs.variables.iface, task_id=task_id,
                                                db=db, log_path=project.configs.folders.scapy_logs))
        return Response(status=201)
    
    @BaseView.route('POST', '/scapy_scan_stop')
    @project_require
    async def stop_scapy(self, request: Request):
        project = await get_project(request=request)
        jobs = list(project.schedulers.get('scapy')._jobs)
        if not len(jobs):
            # ToDo notify client
            await notify_client(request=request, queue_type='message',
                                message={'title': 'Nothing to stop', 'type': 'error',
                                         'text': 'Project have no active scapy scan task'})
            return Response(status=400)
        for job in jobs:
            try:
                await job.soft_stop()
            except Exception as e:
                await notify_client(request=request, queue_type='message',
                                message={'title': 'Sniffing stoping error', 'type': 'error',
                                         'text': str(e)})
                return Response(status=500)
        return Response(status=202)
    
    @BaseView.route('POST', '/scapy_log')
    @project_require
    async def create_scapy_log(self, request: Request):
        params = await request.json()
        log_file = params.pop('log_file')
        data = b64decode(log_file.split(',')[1])
        project = await get_project(request=request)
        scheduler = project.schedulers.get('other')
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        await scheduler.spawn_job(ScapyLogTask(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}', task_id=task_id,
                                               db=db, scapy_logs=project.configs.folders.scapy_logs, data=data, iface=project.configs.variables.iface))
        return Response(status=201)

    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: Request):
        raise NotImplementedError()
    