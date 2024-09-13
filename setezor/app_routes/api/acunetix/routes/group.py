import asyncio
from setezor.modules.acunetix.acunetix_config import Config
import json
from aiohttp.web import Request, Response, json_response
from setezor.app_routes.session import get_project, project_require, get_db_by_session
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest
from setezor.modules.acunetix.target import Target

from setezor.modules.acunetix.group import Group


class AcunetixGroupView:
    @BaseView.route('GET', '/groups/')
    @project_require
    async def get_groups(self, request: PMRequest) -> Response:
        query = request.rel_url.query
        project = await get_project(request=request)
        groups = await project.acunetix_manager.get_groups(name=query.get("acunetix_name"))
        return json_response(status=200, data=groups)

    @BaseView.route('POST', '/groups/')
    @project_require
    async def add_group(self, request: PMRequest):
        query = request.rel_url.query
        project = await get_project(request=request)
        payload = await request.text()
        status, msg = await project.acunetix_manager.add_group(name=query.get("acunetix_name"), payload=payload)
        return json_response(status=status, data=msg)

    @BaseView.route('GET', '/groups/{group_id}/targets/')
    @project_require
    async def get_group_targets(self, request: PMRequest):
        project = await get_project(request=request)
        query = request.rel_url.query
        group_id = request.match_info["group_id"]
        resp = await project.acunetix_manager.get_group_targets(name=query.get("acunetix_name"), group_id=group_id)
        targets_ids = resp['target_id_list']
        tasks = []
        for target_id in targets_ids:
            task = asyncio.create_task(project.acunetix_manager.get_target_by_id(
                name=query.get("acunetix_name"), target_id=target_id))
            tasks.append(task)
        targets = await asyncio.gather(*tasks)
        return json_response(status=200, data=targets)

    @BaseView.route('PUT', '/groups/{group_id}/targets/')
    @project_require
    async def set_group_targets(self, request: PMRequest):
        query = request.rel_url.query
        project = await get_project(request=request)
        group_id = request.match_info["group_id"]
        payload = await request.json()
        status = await project.acunetix_manager.set_group_targets(name=query.get("acunetix_name"),
                                                                  group_id=group_id,
                                                                  payload=payload)
        return json_response(status=status)

    @BaseView.route('PUT', '/groups/{group_id}/proxy/')
    @project_require
    async def update__group_targets_proxy(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        payload: dict = await request.json()
        group_id = request.match_info["group_id"]
        query = request.rel_url.query
        acunetix_name = query.get("acunetix_name")
        status = await project.acunetix_manager.set_group_targets_proxy(name=acunetix_name,
                                                                        group_id=group_id,
                                                                        payload=payload)
        return json_response(status=status)

    '''
    @BaseView.route('GET', '/{group_id}/targets/')
    async def get_group_targets(self, request: PMRequest) -> GroupTargets:
        group_id = request.match_info.get("group_id")
        resp = await send_request(url=f"/api/v1/target_groups/{group_id}/targets", method="GET")
        targets_ids = resp['target_id_list']
        tasks = []
        for target_id in targets_ids:
            task = asyncio.create_task(get_target(target_id))
            tasks.append(task)
        targets = await asyncio.gather(*tasks)
        return json_response(status=200, data={"data": targets})

    @BaseView.route('POST', '/{group_id}/targets/')
    async def add_target_to_group(self, request: PMRequest) -> GroupTargets:
        group_id = request.match_info.get("group_id")
        payload = await request.json()
        target_form = TargetFormBase(**payload)
        data = TargetForm(groups=[group_id], targets=[target_form])
        new_targets = await send_request(url="/api/v1/targets/add", method="POST", data=data.model_dump_json())
        for target in new_targets.get("targets"):
            new_target = Target(**target).model_dump_json()
            return json_response(status=201, data={"data": json.loads(new_target)})

    @BaseView.route('GET', '/{group_id}/vulnerabilities/')
    async def get_group_vulnerabilities(self, request: PMRequest):
        group_id = request.match_info.get("group_id")
        limit = 20
        params = {
            "l": limit,
            "q": f"group_id:{group_id};status:!ignored;status:!fixed;",
            "s": "severity:desc"
        }
        vulnerabilities: list[Vulnerability] = []
        severities: dict[int, str] = {
            0: "Informational",
            1: "Low",
            2: "Medium",
            3: "High",
            4: "Critical",
        }
        while True:
            raw_data = await send_request(url=f"/api/v1/vulnerabilities", method="GET", params=params)
            for vuln in raw_data.get("vulnerabilities"):
                vuln["severity"] = severities[vuln["severity"]]
                vuln["last_seen"] = datetime.datetime.strftime(datetime.datetime.strptime(vuln["last_seen"], "%Y-%m-%dT%H:%M:%S.%f%z"),
                                                               "%d.%m.%Y, %H:%M:%S")
                vulnerabilities.append(vuln)
            pagination = raw_data.get("pagination")
            cursors = pagination["cursors"]
            if len(cursors) == 1:
                return json_response(status=200, data={"data": vulnerabilities})
            params.update({"c": cursors[1]})

    @BaseView.route('GET', '/{group_id}/scans/')
    async def get_scans_of_group(self, request: PMRequest):
        group_id = request.match_info.get("group_id")
        query = request.rel_url.query
        params = json.loads(query.get('params', {}))
        page = int(params.get('page', 1))
        size = int(params.get('size', 10))
        if page == 1:
            params = {"l": size}
        else:
            params = {"l": size, "c": size * (page - 1)}
        params.update({
            "q": f"group_id:{group_id};",
            "s": "start_date:desc"
        })
        raw_data = await send_request(url="/api/v1/scans", method="GET", params=params)
        scans = raw_data.get("scans")
        pagination = raw_data.get("pagination")
        count = pagination.get("count")
        last_page = int(count / size) + 1
        for scan in scans:
            if scan["current_session"]["start_date"]:
                scan["schedule"]["start_date"] = datetime.datetime.strftime(datetime.datetime.strptime(scan["current_session"]["start_date"], "%Y-%m-%dT%H:%M:%S.%f%z"),
                                                                               "%d.%m.%Y, %H:%M:%S")
                continue
            scan["schedule"]["start_date"] = datetime.datetime.strftime(datetime.datetime.strptime(scan["schedule"]["start_date"][:-6], "%Y-%m-%dT%H:%M:%S"),
                                                                               "%d.%m.%Y, %H:%M:%S")
        return json_response(status=200, data={"data": scans, "last_page": last_page})

    @BaseView.route('POST', '/{group_id}/scans/')
    async def create_scan_for_group(self, request: PMRequest):
        group_id = request.match_info.get("group_id")
        payload = await request.json()
        group_scan = GroupScanStart(group_id=group_id, **payload)
        interval = datetime.timedelta(
            hours=group_scan.interval.hour, minutes=group_scan.interval.minute)
        scan_speed_json = json.dumps({
            "scan_speed": group_scan.scan_speed
        })
        raw_targets = await send_request(url=f"/api/v1/target_groups/{group_scan.group_id}/targets", method="GET")
        targets = GroupTargets(**raw_targets)

        scan_speed_reqs = []
        for target_id in targets.target_id_list:
            task = asyncio.create_task(send_request(
                url=f"/api/v1/targets/{target_id}/configuration", method="PATCH", data=scan_speed_json))
            scan_speed_reqs.append(task)
        await asyncio.gather(*scan_speed_reqs)

        raw_data = {
            "profile_id": group_scan.profile_id,
            "incremental": False,
            "schedule": {
                "disable": False,
                "start_date": "",
                "time_sensitive": True
            },
            "target_id": ""
        }

        scans = []

        for index, target_id in enumerate(targets.target_id_list):
            if index == 0:
                raw_data["schedule"]["start_date"] = convert_to_datetime_for_scan(
                    date=group_scan.date, time=group_scan.start_time)
            else:
                raw_data["schedule"]["start_date"] = convert_to_datetime_for_scan(
                    date=group_scan.date, time=group_scan.start_time, interval=interval)
                interval = get_new_interval(interval, group_scan.interval)
            raw_data["target_id"] = target_id

            data = json.dumps(raw_data)
            task = asyncio.create_task(send_request(
                url=f"/api/v1/scans", method="POST", data=data))
            scans.append(task)
        result = await asyncio.gather(*scans)
        tasks = []
        for raw_scan in result:
            task = asyncio.create_task(get_scan(raw_scan["scan_id"]))
            tasks.append(task)
        scans = await asyncio.gather(*tasks)
        for scan in scans:
            if scan["current_session"]["start_date"]:
                scan["schedule"]["start_date"] = datetime.datetime.strftime(datetime.datetime.strptime(scan["current_session"]["start_date"], "%Y-%m-%dT%H:%M:%S.%f%z"),
                                                                               "%d.%m.%Y, %H:%M:%S")
                continue
            scan["schedule"]["start_date"] = datetime.datetime.strftime(datetime.datetime.strptime(scan["schedule"]["start_date"][:-6], "%Y-%m-%dT%H:%M:%S"),
                                                                               "%d.%m.%Y, %H:%M:%S")
        return json_response(status=201, data={"data": scans})

        '''
