import aiofiles
from requests import Response
from setezor.app_routes.api.base_web_view import BaseView
from setezor.app_routes.session import get_db_by_session, get_project, project_require
from setezor.modules.acunetix.acunetix_config import Config
from setezor.modules.acunetix.target import Target
from setezor.modules.application.pm_request import PMRequest
from aiohttp.web import json_response

class AcunetixConfigView:
    @BaseView.route('GET', '/config/')
    @project_require
    async def get_config(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        return json_response(status=200, data=project.acunetix_manager.apis)

    @BaseView.route('POST', '/config/')
    @project_require
    async def add_config(self, request: PMRequest) -> Response:
        payload = await request.json()
        result = await Config.health_check(payload)
        if result.get("code"):
            status = 500
        else:
            status = 200
        if status == 500:
            return json_response(status=status)

        project = await get_project(request=request)
        db = await get_db_by_session(request=request)
        project.acunetix_manager.add_api(payload)
        acunetix_name = payload.get("name")
        targets = await project.acunetix_manager.get_targets(name=acunetix_name)
        for target in targets:
            data = Target.parse_url(url = target["address"])
            resource_obj = db.resource.get_or_create(**data)
            db.resource.update_by_id(id=resource_obj.id, to_update={"acunetix_id": target["target_id"]}, merge_mode="replace")
        return json_response(status=status)
