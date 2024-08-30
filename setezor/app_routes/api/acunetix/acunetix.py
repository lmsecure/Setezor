from setezor.app_routes.api.base_web_view import BaseView
from .routes.group import AcunetixGroupView
from .routes.target import AcunetixTargetView
from .routes.scan import AcunetixScanView
from .routes.report import AcunetixReportView
from .routes.acunetix_config import AcunetixConfigView

class AcunetixView(BaseView,
                   AcunetixGroupView,
                   AcunetixTargetView,
                   AcunetixScanView,
                   AcunetixReportView,
                   AcunetixConfigView):
    endpoint = '/acunetix'
    queries_path = 'acunetix'

'''
    @BaseView.route('GET', '/groups/{group_id}/targets/')
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

    @BaseView.route('POST', '/groups/{group_id}/targets/')
    async def add_target_to_group(self, request: PMRequest) -> GroupTargets:
        group_id = request.match_info.get("group_id")
        payload = await request.json()
        target_form = TargetFormBase(**payload)
        data = TargetForm(groups=[group_id], targets=[target_form])
        new_targets = await send_request(url="/api/v1/targets/add", method="POST", data=data.model_dump_json())
        for target in new_targets.get("targets"):
            new_target = Target(**target).model_dump_json()
            return json_response(status=201, data={"data": json.loads(new_target)})

    @BaseView.route('GET', '/groups/{group_id}/vulnerabilities/')
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

    @BaseView.route('GET', '/groups/{group_id}/scans/')
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
        if not count % size:
            last_page = count // size
        else:
            last_page = count // size + 1
        for scan in scans:
            if scan["current_session"]["start_date"]:
                scan["schedule"]["start_date"] = datetime.datetime.strftime(datetime.datetime.strptime(scan["current_session"]["start_date"], "%Y-%m-%dT%H:%M:%S.%f%z"),
                                                                            "%d.%m.%Y, %H:%M:%S")
                continue
            scan["schedule"]["start_date"] = datetime.datetime.strftime(datetime.datetime.strptime(scan["schedule"]["start_date"][:-6], "%Y-%m-%dT%H:%M:%S"),
                                                                        "%d.%m.%Y, %H:%M:%S")
        return json_response(status=200, data={"data": scans, "last_page": last_page})

    @BaseView.route('GET', '/reports/')
    async def get_reports_by_date(self, request: PMRequest):
        limit = 100
        query = request.rel_url.query
        # params = json.loads(query.get('params', {}))
        # print(params)
        # prev_day = date - datetime.timedelta(days=1)
        # next_day = date + datetime.timedelta(days=1)
        params = {
            "l": limit,
            "s": "created:desc",
            # "q": f"created:>={prev_day}T19:00:00.000Z;created:<={next_day}T19:00:00.000Z;"
        }
        raw_data = await send_request(url="/api/v1/reports", method="GET", params=params)

        pagination = raw_data.get("pagination")
        count = pagination.get("count")
        reports = raw_data.get("reports")
        for report in reports:
            report['generation_date'] = datetime.datetime.strftime(datetime.datetime.strptime(report['generation_date'], "%Y-%m-%dT%H:%M:%S.%f%z"),
                                                                   "%d.%m.%Y, %H:%M:%S")
        return json_response(status=201, data={"data": reports})
'''