import aiofiles
from requests import Response
from setezor.app_routes.api.base_web_view import BaseView
from setezor.app_routes.session import get_db_by_session, get_project, project_require
from setezor.modules.acunetix.acunetix_config import Config
from setezor.modules.acunetix.target import Target
from setezor.modules.application.pm_request import PMRequest
from aiohttp.web import json_response
import json


class AcunetixConfigView:
    @BaseView.route('GET', '/config/')
    @project_require
    async def get_config(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)
        data = json.loads(credentials)
        return json_response(status=200, data={"data": data})

    @BaseView.route('POST', '/config/')
    @project_require
    async def set_config(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        payload = await request.text()
        db = await get_db_by_session(request=request)
        await Config.set(path=project.configs.files.acunetix_configs, payload=payload)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        result = await Config.health_check(credentials)
        if result.get("code"):
            status = 500
        else:
            status = 200
        if status == 500:
            return json_response(status=status)
        
        all_targets = []
        targets, count = await Target.get_all(params={"l":100},credentials=credentials)
        all_targets.extend(targets)
        i = 1
        while len(all_targets) < count:
            targets, _ = await Target.get_all(params={"l":100,"c": 100 * i},credentials=credentials)
            all_targets.extend(targets)
            i += 1
        for target in all_targets:
            data = Target.parse_url(url = target["address"])
            resource_obj = db.resource.get_or_create(**data)
            db.resource.update_by_id(id=resource_obj.id, to_update={"acunetix_id": target["target_id"]}, merge_mode="replace")
        return json_response(status=status)
