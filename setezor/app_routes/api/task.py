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
from setezor.tasks.wappalyzer_task import Wappalyzer
from setezor.tasks.cve_refresh_task import CVERefresher
from setezor.tasks.cve_task import Cve
from setezor.tasks.snmp_brute_community_string_task import SNMP_brute_community_string_task
from setezor.tasks.snmp_crawler_task import SNMP_crawler_task

from setezor.tasks.screenshot_task import ScreenshotTask
from setezor.tasks.task_status import TaskStatus
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest
from setezor.modules.project_manager.manager import ProjectManager
from setezor.tools.ip_tools import get_ipv4, get_mac
from sqlalchemy import desc
import datetime
from setezor.tools import url_tools

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
    
    @BaseView.route('POST', '/wappalyzer_log_parse')
    @project_require
    async def create_wappalyzer_task(self, request: PMRequest):
        params: dict = await request.json()
        log_file = b64decode(params.pop('log_file').split(',')[1]).decode()
        if not log_file:
            await notify_client(request=request, queue_type='message',
                        message={'title': f'Error"', 'type': 'error',
                        'text': f'Empty file failed'})
            return Response(status=400)
        json_file = json.loads(log_file)
        groups = params.pop('groups')
        params.update({"task" : Wappalyzer.__name__})
        project = await get_project(request=request)
        db = project.db
        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params, ensure_ascii=False), ret='id')
        scheduler = project.schedulers.get('other')
        await scheduler.spawn_job(Wappalyzer(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}',
                                             task_id=task_id, db=db, data=json_file, groups=groups))
        return Response(status=201)
    

    @BaseView.route('POST', '/cve_task')
    @project_require
    async def create_cve_task(self, request: PMRequest):
        project = await get_project(request=request)
        source = 'vulners'
        db = project.db
        session = db.db.create_session()
        list_soft_obj = session.query(db.software.model).where(db.software.model.cpe23 != None).all()
        for soft_obj in list_soft_obj:
            list_cpe = (soft_obj.cpe23 or '').split(', ')
            for cpe in list_cpe:
                if cpe[:7] == "cpe:2.3":
                    params = json.dumps({'source' : source, 'cpe' : cpe}, ensure_ascii=False)
                    task = session.query(db.task.model).filter(db.task.model.params == json.dumps(params), 
                                                            db.task.model.status == "FINISHED")\
                                                                .order_by(desc(db.task.model.started)).first()
                    if task:
                        val = datetime.datetime.now() - task.started
                        if val.seconds < 3600: # проверка, что для данного cpe23 повторный запуск был не раньше часа
                            await notify_client(request=request, queue_type='message',
                                message={'title': f'Warning', 'type': 'warning',
                                        'text': f'Retry after {(3600 - val.seconds) // 60 + 1} minutes. cpe = {cpe}'})
                            continue
                    task_id = db.task.write(status=TaskStatus.in_queue, params=params, ret='id')
                    scheduler = project.schedulers.get('cve_vulners')
                    await scheduler.spawn_job(Cve(observer=project.observer, scheduler=scheduler, name=f'Task {task_id}', db=db,
                                                task_id=task_id, log_path=project.configs.folders.cve_logs, cpe=cpe, source=source, list_res_id=[obj.id for obj in soft_obj._resource]))
        return Response(status=201)
    

    @BaseView.route('POST','/refresh_cve')
    @project_require
    async def refresh_cve_task(self, request: PMRequest):
        project = await get_project(request=request)
        if not (token := project.configs.variables.search_vulns_token):
            return json_response(status=500)
        db = project.db
        scheduler = project.schedulers.get('search-vulns')
        session = db.db.create_session()
        softwares = session.query(db.software.model).filter(db.software.model.cpe23 != None).all()
        
        for soft in softwares:
            cpe_list = soft.cpe23.split(", ")
            for cpe23 in cpe_list:
                params = json.dumps({"source":"search-vulns","cpe":cpe23}, ensure_ascii=False)
                task = session.query(db.task.model).filter(db.task.model.params == json.dumps(params), 
                                                        db.task.model.status == "FINISHED")\
                                                            .order_by(desc(db.task.model.started)).first()
                if task:
                    val = datetime.datetime.now() - task.started
                    if val.seconds < 3600: # проверка, что для данного cpe23 повторный запуск был не раньше часа
                        await notify_client(request=request, queue_type='message',
                            message={'title': f'Warning', 'type': 'warning',
                                    'text': f'Retry after {(3600 - val.seconds) // 60 + 1} minutes. cpe = {cpe23}'})
                        continue
                resource_softwares = [obj.id for obj in soft._resource]
                if not resource_softwares:
                    await notify_client(request=request, queue_type='message',
                            message={'title': f'Error"', 'type': 'error',
                                    'text': f'No resources found for cpe="{cpe23}'})
                    continue
                task_id = db.task.write(status=TaskStatus.in_queue, params=params, ret='id')
                await scheduler.spawn_job(CVERefresher(observer=project.observer,scheduler=scheduler, 
                                                    name=f'Task {task_id}',task_id=task_id, 
                                                    db=db,token=token,cpe23=cpe23,res_softs_ids = resource_softwares))
        return Response(status=201)
    
    @BaseView.route('POST', "/screenshot")
    @project_require
    async def generate_screenshot(self, request: PMRequest):
        body = await request.json()
        url = body.get("url")
        timeout = float(body.get("timeout"))
        if not "http" in url:
            await notify_client(request=request, queue_type='message',
                                message={'title': 'Error', 'type': 'error',
                                         'text': 'Invalid URL. URL should have scheme(http/https)'})
            return json_response(status=400)
        try:
            parsed_url = url_tools.parse_url(url)
        except Exception as e:
            await notify_client(request=request, queue_type='message',
                                message={'title': 'Error', 'type': 'error',
                                         'text': str(e)})
            return json_response(status=400)
        project = await get_project(request=request)
        screenshots_folder = project.configs.folders.screenshots
        db = project.db
        params = json.dumps(body, ensure_ascii=False)
        task_id = db.task.write(
            status=TaskStatus.in_queue, params=params, ret='id')
        scheduler = project.schedulers.get('screenshoter')
        await scheduler.spawn_job(ScreenshotTask(observer=project.observer, scheduler=scheduler,
                                                 name=f'Task {task_id}', task_id=task_id,
                                                 db=db, url=url, screenshots_folder=screenshots_folder,
                                                 timeout=timeout,
                                                 **parsed_url))
        return json_response(data=True)


    @BaseView.route('POST', '/SNMP_brute_communitystring')
    @project_require
    async def SNMP_brute_comunitystring_task(self, request: PMRequest):
        project = await get_project(request=request)
        db = project.db
        scheduler = project.schedulers.get('other')
        params: dict = await request.json()

        ip = params.get("ip")
        community_strings_lst = []
        if params.get("community_string_lst"):
            community_strings_lst = b64decode(params.pop("community_string_lst").split(',')[1]).decode().split('\n')

        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params), ret='id')
        await scheduler.spawn_job(SNMP_brute_community_string_task(observer=project.observer,scheduler=scheduler, 
                                                    name=f'Task {task_id}',task_id=task_id, 
                                                    db=db, ip=ip, community_strings=community_strings_lst))
        
        
        return Response(status=201)
    

    @BaseView.route('POST', '/SNMP_crawler')
    @project_require
    async def SNMP_crawler_task(self, request: PMRequest):
        project = await get_project(request=request)
        db = project.db
        scheduler = project.schedulers.get('other')
        params: dict = await request.json()

        ip = params.get("ip")
        community_string = params.get("community_string")

        print('\n', '-' * 30, 'SNMP_crawler_task' '-' * 30)
        print(f"{params = }")

        task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(params), ret='id')
        await scheduler.spawn_job(SNMP_crawler_task(observer=project.observer,scheduler=scheduler, 
                                            name=f'Task {task_id}',task_id=task_id, 
                                            db=db, ip=ip, community_string=community_string))
        
        return Response(status=201)