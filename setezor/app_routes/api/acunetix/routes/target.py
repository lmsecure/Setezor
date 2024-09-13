import json
from setezor.modules.acunetix.acunetix_config import Config
from aiohttp.web import Request, Response, json_response
from setezor.app_routes.session import get_db_by_session, get_project, project_require
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest
from setezor.modules.acunetix.target import Target
import io
import csv


class AcunetixTargetView:
    @BaseView.route('GET', '/targets/')
    @project_require
    async def get_all_targets(self, request: PMRequest) -> Response:
        query = request.rel_url.query
        project = await get_project(request=request)
        targets = await project.acunetix_manager.get_targets(query.get("acunetix_name"))
        return json_response(status=200, data=targets)

    @BaseView.route('POST', '/targets/')
    @project_require
    async def add_target(self, request: PMRequest) -> Response:
        query = request.rel_url.query
        project = await get_project(request=request)
        db = await get_db_by_session(request=request)
        payload: dict = await request.json()
        acunetix_name = query.get("acunetix_name")
        for i in range(len(payload) // 2):
            raw_payload = {
                "address": payload[f"address{i+1}"],
                "description": payload[f"description{i+1}"],
                "group_id": payload["group_id"]
            }
            raw_address = raw_payload["address"]
            data = Target.parse_url(url=raw_address)
            resource_obj = db.resource.get_or_create(**data)
            status, msg = await project.acunetix_manager.add_target(name=acunetix_name, payload=raw_payload)
            if status:
                db.resource.update_by_id(id=resource_obj.id, to_update={
                    "acunetix_id": msg["targets"][0]["target_id"]}, merge_mode="replace")
        return json_response(status=status, data={"data": msg})

    @BaseView.route('POST', '/targets/import_csv/')
    @project_require
    async def import_targets_from_csv(self, request: PMRequest) -> Response:
        query = request.rel_url.query
        data = await request.post()
        project = await get_project(request=request)
        db = await get_db_by_session(request=request)
        group_id = data.get("group_id")
        csv_file = data.get('targets_csv')
        acunetix_name = query.get("acunetix_name")
        data = csv.reader(io.StringIO(csv_file.file.read().decode()))
        raw_payload = {
            "address": "",
            "description": "",
            "group_id": group_id
        }
        for line in data:
            addr = line[0]
            raw_payload["address"] = addr
            data = Target.parse_url(url=addr)
            resource_obj = db.resource.get_or_create(**data)
            status, msg = await project.acunetix_manager.add_target(name=acunetix_name, payload=raw_payload)
            if status:
                db.resource.update_by_id(id=resource_obj.id, to_update={
                    "acunetix_id": msg["targets"][0]["target_id"]}, merge_mode="replace")
        return json_response(status=204)

    @BaseView.route('DELETE', '/targets/{target_id}/')
    @project_require
    async def delete_target(self, request: PMRequest) -> Response:
        query = request.rel_url.query
        acunetix_name = query.get("acunetix_name")
        project = await get_project(request=request)
        target_id = request.match_info["target_id"]
        status, msg = await project.acunetix_manager.delete_target(name=acunetix_name, target_id=target_id)
        return json_response(status=status, data={"data": msg})

    @BaseView.route('PUT', '/targets/{target_id}/proxy/')
    @project_require
    async def update_target_proxy(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        payload: dict = await request.json()
        target_id = request.match_info["target_id"]
        query = request.rel_url.query
        acunetix_name = query.get("acunetix_name")
        status = await project.acunetix_manager.set_target_proxy(name=acunetix_name, target_id=target_id, payload=payload)
        return json_response(status=status)

    @BaseView.route('PUT', '/targets/{target_id}/cookies/')
    @project_require
    async def update_cookies(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        payload: dict = await request.json()
        target_id = request.match_info["target_id"]
        query = request.rel_url.query
        acunetix_name = query.get("acunetix_name")
        status = await project.acunetix_manager.set_target_cookies(name=acunetix_name, target_id=target_id, payload=payload)
        return json_response(status=status)

    @BaseView.route('PUT', '/targets/{target_id}/headers/')
    @project_require
    async def update_headers(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        payload: dict = await request.json()
        target_id = request.match_info["target_id"]
        query = request.rel_url.query
        acunetix_name = query.get("acunetix_name")
        status = await project.acunetix_manager.set_target_headers(name=acunetix_name, target_id=target_id, payload=payload)
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
