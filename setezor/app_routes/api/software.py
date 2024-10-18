from aiohttp.web import Request, Response, json_response
from setezor.app_routes.session import project_require, get_db_by_session, get_project
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest
from setezor.database.models import Resource


class SoftwareView(BaseView):
    endpoint = '/software'
    queries_path = 'software'

    @BaseView.route('GET', '/')
    @project_require
    async def list(self, request: PMRequest) -> Response:
        db = await get_db_by_session(request=request)
        softwares = db.software.get_all()
        result = []
        for software in softwares:
            if not software["product"]:
                continue
            result.append(
                {
                    "id": software["id"],
                    "vendor": software["vendor"],
                    "product": software["product"],
                    "version": software["version"],
                }
            )
        return json_response(status=200, data=result)
