import json
from setezor.app_routes.api.base_web_view import BaseView
from setezor.app_routes.session import get_db_by_session, get_project, project_require
from setezor.modules.acunetix.target import Target
from setezor.modules.application.pm_request import PMRequest
from setezor.tasks.acunetix_scan_task import AcunetixScanTask
from setezor.tasks.task_status import TaskStatus

from ..schemes.scan import GroupScanStart, ScanningProfile, Scan, ScanResult
from ..schemes.report import ReportCreate
from ..schemes.vulnerability import Vulnerability
from aiohttp.web import Request, Response, json_response
from setezor.modules.acunetix.scan import Scan
from setezor.modules.acunetix.acunetix_config import Config


class AcunetixScanView:
    @BaseView.route('GET', '/scans/')
    @project_require
    async def get_scans(self, request: PMRequest):
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)
        query = request.rel_url.query
        params = json.loads(query.get('params', {}))
        page = int(params.get('page', 1))
        size = int(params.get('size', 10))
        if page == 1:
            params = {"l": size}
        else:
            params = {"l": size, "c": size * (page - 1)}
        params.update({
            "s": "start_date:desc"
        })
        scans, count = await Scan.get_all(params=params, credentials=credentials)
        if not count % size:
            last_page = count // size
        else:
            last_page = count // size + 1
        return json_response(status=200, data={"data": scans, "last_page": last_page})

    @BaseView.route('POST', '/scans/')
    @project_require
    async def create_scan(self, request: PMRequest):
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)
        db = await get_db_by_session(request=request)
        payload = await request.json()
        raw_data = []  # заглушка
        if payload.get("group_id"):
            raw_data = await Scan.create_for_group(payload=payload, credentials=credentials)
        if payload.get("target_id"):
            raw_data = await Scan.create_for_target(payload=payload, credentials=credentials)
        if payload.get("target_db_id"):
            target_db_id = payload.get("target_db_id")
            ip_obj = db.ip.get_by_id(id=target_db_id)
            payload["target_ip_address"] = ip_obj["ip"]
            new_targets = Target.create_urls(payload)
            payload["target_ids"] = []
            for target in new_targets:
                data = Target.parse_url(url=target)
                resource_obj = db.resource.get_or_create(**data)
                payload["address"] = target
                status, msg = await Target.create(payload=payload, credentials=credentials)
                if status:
                    acunetix_id = msg["targets"][0]["target_id"]
                    db.resource.update_by_id(id=resource_obj.id, to_update={"acunetix_id": acunetix_id}, merge_mode="replace")
                    payload["target_ids"].append(acunetix_id)
            raw_data = await Scan.create_for_db_obj(payload=payload, credentials=credentials)

        for status, scan in raw_data:
            target_id = scan.get("target_id")
            scan_id = scan.get("scan_id")
            task_id = db.task.write(status=TaskStatus.in_queue, params=json.dumps(
                payload, ensure_ascii=False), ret='id')
            scheduler = project.schedulers.get('other')
            await scheduler.spawn_job(AcunetixScanTask(observer=project.observer,
                                                       scheduler=scheduler,
                                                       name=f'Task {task_id}',
                                                       target_id=target_id,
                                                       scan_id=scan_id,
                                                       credentials=credentials,
                                                       db=db,
                                                       task_id=task_id))
        return json_response(status=201)


'''
async def get_vulnerabilities_of_scan(scan_id: str) -> list[Vulnerability]:
    scan_results: list[ScanResult] = await get_list_of_values(url=f"/api/v1/scans/{scan_id}/results", scheme=ScanResult, key="results")
    tasks = []
    params = {
        "q": "status:!ignored;status:!fixed;",
    }
    for scan_result in scan_results:
        tasks.append(asyncio.create_task(get_list_of_values(
            url=f"/api/v1/scans/{scan_id}/results/{scan_result.result_id}/vulnerabilities", scheme=Vulnerability, key="vulnerabilities", query_params=params)))
    vuln_scan_list = await asyncio.gather(*tasks)
    vulnerabilities = []
    for sub_vulns in vuln_scan_list:
        vulnerabilities += sub_vulns
    return vulnerabilities
'''
