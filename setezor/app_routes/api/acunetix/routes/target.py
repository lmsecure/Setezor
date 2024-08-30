import json
from setezor.modules.acunetix.acunetix_config import Config
from aiohttp.web import Request, Response, json_response
from setezor.app_routes.session import get_db_by_session, get_project, project_require
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest
from setezor.modules.acunetix.target import Target


class AcunetixTargetView:
    @BaseView.route('GET', '/targets/')
    @project_require
    async def get_all_targets(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)
        query = request.rel_url.query
        params = json.loads(query.get('params', "{}"))
        page = int(params.get('page', 1))
        size = int(params.get('size', 10))
        sort = params.get('sort', {})
        if page == 1:
            params = {"l": size}
        else:
            params = {"l": size, "c": size * (page - 1)}
        if sort:
            params.update({"s": f"{sort[0]['field']}:{sort[0]['dir']}"})
        targets, count = await Target.get_all(params=params, credentials=credentials)
        if not count % size:
            last_page = count // size
        else:
            last_page = count // size + 1
        return json_response(status=200, data={"data": targets, "last_page": last_page})

    @BaseView.route('POST', '/targets/')
    @project_require
    async def add_target(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)
        db = await get_db_by_session(request=request)
        payload: dict = await request.json()
        raw_address = payload["address"]
        data = Target.parse_url(url = raw_address)
        resource_obj = db.resource.get_or_create(**data)
        status, msg = await Target.create(payload=payload, credentials=credentials)
        if status:
            db.resource.update_by_id(id=resource_obj.id, to_update={
                                     "acunetix_id": msg["targets"][0]["target_id"]}, merge_mode="replace")
        return json_response(status=status, data={"data": msg})

    @BaseView.route('DELETE', '/targets/{target_id}/')
    @project_require
    async def delete_target(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)
        target_id = request.match_info["target_id"]
        status, msg = await Target.delete(id=target_id, credentials=credentials)
        return json_response(status=status, data={"data": msg})

    @BaseView.route('PUT', '/targets/{target_id}/proxy/')
    @project_require
    async def update_proxy(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)
        payload: dict = await request.json()
        target_id = request.match_info["target_id"]
        status = await Target.set_proxy(id=target_id, payload=payload, credentials=credentials)
        return json_response(status=status)

    @BaseView.route('PUT', '/targets/{target_id}/cookies/')
    @project_require
    async def update_cookies(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)
        payload: dict = await request.json()
        target_id = request.match_info["target_id"]
        status = await Target.set_cookies(id=target_id, payload=payload, credentials=credentials)
        return json_response(status=status)

    @BaseView.route('PUT', '/targets/{target_id}/headers/')
    @project_require
    async def update_headers(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)
        payload: dict = await request.json()
        target_id = request.match_info["target_id"]
        status = await Target.set_headers(id=target_id, payload=payload, credentials=credentials)
        return json_response(status=status)


'''
async def add_target(target_form: TargetForm) -> list[Target]:
    new_targets = await send_request(url="/api/v1/targets/add", method="POST", data=target_form.model_dump_json())
    result: list[Target] = []
    for target in new_targets.get("targets"):
        result.append(Target(**target))
    return result


async def get_target(credentials: dict, target_id: str) -> Target:

    return await send_request(base_url=credentials["url"],
                              token=credentials["token"],
                              url=f"/api/v1/targets/{target_id}",
                              method="GET")
'''
