import json
from base64 import b64decode

from aiohttp.web import Response, json_response
from setezor.app_routes.session import (
    project_require,
    get_project,
    notify_client,
    notify_clients_in_project,
    get_db_by_session
)
from setezor.tasks.nmap_logs_task import NmapLogTask
from setezor.tasks.nmap_scan_task import NmapScanTask
from setezor.tasks.scapy_scan_task import ScapyScanTask
from setezor.tasks.scapy_logs_task import ScapyLogTask
from setezor.tasks.masscan_scan_task import MasscanScanTask
from setezor.tasks.masscan_logs_task import (
    MasscanJSONLogTask,
    MasscanXMLLogTask,
    MasscanListLogTask
)
from setezor.tasks.dns_task import DNSTask
from setezor.tasks.domain_task import SdFindTask
from setezor.tasks.whois_task import WhoisTask
from setezor.tasks.cert_task import CertInfoTask

from setezor.tasks.screenshot_by_ip_task import ScreenshotFromIPTask
from setezor.tasks.task_status import TaskStatus
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest
from setezor.modules.project_manager.manager import ProjectManager
from setezor.tools.ip_tools import get_ipv4, get_mac

class TaskView(BaseView):
    endpoint = '/task'
    queries_path = 'task'

    @BaseView.route('POST', '/nmap_scan')
    @project_require
    async def create_nmap_scan(self, request: PMRequest):
        params: dict = await request.json()
        project = await get_project(request=request)
        db = project.db
        iface = params.pop('iface').strip()
        agent_id = params.pop('agent_id')
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        scheduler = project.schedulers.get('nmap')
        await scheduler.spawn_job(NmapScanTask(agent_id=agent_id, observer=project.observer, 
                                               scheduler=scheduler, name=f'Task {task_id}',
                                               command=' '.join(params.values()), iface=iface,
                                               db = db, nmap_logs=project.configs.folders.nmap_logs, task_id=task_id))
        return Response(status=201)
    
    @BaseView.route('POST', '/nmap_log')
    @project_require
    async def create_nmap_log(self, request: PMRequest):
        params = await request.json()
        log_file = params.pop('log_file')
        ip = params.pop('ip')
        mac = params.pop('mac')
        agent_id = params.pop('agent_id')
        data = b64decode(log_file.split(',')[1])
        project = await get_project(request=request)
        scheduler = project.schedulers.get('other')
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        await scheduler.spawn_job(NmapLogTask(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}',
                                              data=data, scanning_ip=ip, scanning_mac=mac, agent_id=agent_id,
                                              db=db, nmap_logs=project.configs.folders.nmap_logs, task_id=task_id))
        return Response(status=201)
        
    @BaseView.route('POST', '/scapy_scan')
    @project_require
    async def create_scapy_scan(self, request: PMRequest):
        project = await get_project(request=request)
        scheduler = project.schedulers.get('scapy')
        if scheduler.active_count >= scheduler.limit:
            await notify_client(request=request, queue_type='message',
                                message={'title': 'Task alredy running', 'type': 'warning',
                                         'text': 'Scanning by scapy already running'})
            return json_response(status=409, data={'message': 'Scanning by scapy already running'})
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params='', ret='id')
        params = await request.json()
        iface = params['iface']
        agent_id = params.pop('agent_id')
        await scheduler.spawn_job(ScapyScanTask(agent_id=agent_id, observer=project.observer, 
                                                scheduler=scheduler, name=f'Task {task_id}',
                                                iface=iface, task_id=task_id,
                                                db=db, log_path=project.configs.folders.scapy_logs))
        return Response(status=201)
    
    @BaseView.route('POST', '/scapy_scan_stop')
    @project_require
    async def stop_scapy(self, request: PMRequest):
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
    async def create_scapy_log(self, request: PMRequest):
        params = await request.json()
        ip = params.pop('ip')
        mac = params.pop('mac')
        log_file = params.pop('log_file')
        agent_id = params.pop('agent_id')
        data = b64decode(log_file.split(',')[1])
        project = await get_project(request=request)
        scheduler = project.schedulers.get('other')
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        await scheduler.spawn_job(ScapyLogTask(agent_id=agent_id, observer=project.observer, scheduler=scheduler, name=f'Task {task_id}', task_id=task_id,
                                               db=db, scapy_logs=project.configs.folders.scapy_logs, data=data, scanning_ip=ip, scanning_mac=mac))
        return Response(status=201)
    
    @BaseView.route('POST', '/masscan_scan')
    @project_require
    async def create_masscan_scan(self, request: PMRequest):
        params: dict = await request.json()
        iface = params.pop('iface').strip()
        project = await get_project(request=request)
        db = project.db
        ip = get_ipv4(iface)
        mac = get_mac(iface)
        agent_id = params.pop('agent_id')
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        scheduler = project.schedulers.get('masscan')
        await scheduler.spawn_job(MasscanScanTask(agent_id=agent_id, observer=project.observer, scheduler=scheduler, name=f'Task {task_id}',
                                               arguments=params.get('arguments', {}), scanning_ip=ip, scanning_mac=mac,
                                               db=db, masscan_log_path=project.configs.folders.masscan_logs, task_id=task_id))
        return Response(status=201)
    
    @BaseView.route('POST', '/masscan_json_log')
    @project_require
    async def create_masscan_json_log(self, request: PMRequest):
        params: dict = await request.json()
        ip = params.pop('ip')
        mac = params.pop('mac')
        log_file: str = params.pop('log_file')
        agent_id = params.pop('agent_id')
        data = b64decode(log_file.split(',')[1]).decode()
        project = await get_project(request=request)
        scheduler = project.schedulers.get('other')
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        await scheduler.spawn_job(MasscanJSONLogTask(agent_id=agent_id, observer=project.observer, scheduler=scheduler, name=f'Task {task_id}', task_id=task_id,
                                               db=db, masscan_log_path=project.configs.folders.masscan_logs, input_data=data, scanning_ip=ip, scanning_mac=mac))
        return Response(status=201)

    @BaseView.route('POST', '/masscan_xml_log')
    @project_require
    async def create_masscan_xml_log(self, request: PMRequest):
        params: dict = await request.json()
        ip = params.pop('ip')
        mac = params.pop('mac')
        log_file: str = params.pop('log_file')
        agent_id = params.pop('agent_id')
        data = b64decode(log_file.split(',')[1]).decode()
        project = await get_project(request=request)
        scheduler = project.schedulers.get('other')
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        await scheduler.spawn_job(MasscanXMLLogTask(agent_id=agent_id, observer=project.observer, scheduler=scheduler, name=f'Task {task_id}', task_id=task_id,
                                               db=db, masscan_log_path=project.configs.folders.masscan_logs, input_data=data, scanning_ip=ip, scanning_mac=mac))
        return Response(status=201)

    @BaseView.route('POST', '/masscan_list_log')
    @project_require
    async def create_masscan_list_log(self, request: PMRequest):
        params: dict = await request.json()
        ip = params.pop('ip')
        mac = params.pop('mac')
        log_file: str = params.pop('log_file')
        agent_id = params.pop('agent_id')
        data = b64decode(log_file.split(',')[1]).decode()
        project = await get_project(request=request)
        scheduler = project.schedulers.get('other')
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        await scheduler.spawn_job(MasscanListLogTask(agent_id=agent_id, observer=project.observer, scheduler=scheduler, name=f'Task {task_id}', task_id=task_id,
                                               db=db, masscan_log_path=project.configs.folders.masscan_logs, input_data=data, scanning_ip=ip, scanning_mac=mac))
        return Response(status=201)

    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: PMRequest):
        raise NotImplementedError()
    
    @BaseView.route('POST', '/dns_info')
    @project_require
    async def create_dns_info(self, request: PMRequest):
        params: dict = await request.json()
        params.update({"task":DNSTask.__name__})
        project = await get_project(request=request)
        db = project.db
        domain = params.get('targetDOMAIN') #домен или ip
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        scheduler = project.schedulers.get('other')
        await scheduler.spawn_job(DNSTask(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}',
                                               domain= domain,
                                               db=db, task_id=task_id))
        return Response(status=201)
    
    @BaseView.route('POST', '/sd_find')
    @project_require
    async def create_sd_find(self, request: PMRequest):
        params: dict = await request.json()
        params.update({"task":SdFindTask.__name__})
        project = await get_project(request=request)
        db = project.db
        domain = params.get('targetDOMAIN')
        crtshtumb = params.get('crt_sh')
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        scheduler = project.schedulers.get('other')
        await scheduler.spawn_job(SdFindTask(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}',
                                               task_id=task_id, domain = domain, crtshtumb = crtshtumb,
                                               db=db))
        return Response(status=201)
    
    @BaseView.route('POST', '/whois')
    @project_require
    async def create_whois(self, request: PMRequest):
        params: dict = await request.json()
        params.update({"task":WhoisTask.__name__})
        project = await get_project(request=request)
        db = project.db
        target = str(params.get('Target')) #домен или ip
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        scheduler = project.schedulers.get('other')
        await scheduler.spawn_job(WhoisTask(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}',
                                               target = target,
                                               db=db, task_id=task_id))
        return Response(status=201)
    
    @BaseView.route('POST', '/cert_info')
    @project_require
    async def create_cert_info(self, request: PMRequest):
        params: dict = await request.json()
        params.update({"task":CertInfoTask.__name__})
        project = await get_project(request=request)
        db = project.db
        target = params.get('Target') #домен или ip
        port = params.get('Port')
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        scheduler = project.schedulers.get('other')
        await scheduler.spawn_job(CertInfoTask(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}',
                                               certificates_folder = project.configs.folders.certificates_folder, target = target, db=db, task_id=task_id, port=port))
        return Response(status=201)
    
    