from aiohttp.web import Request, Response, json_response
from setezor.app_routes.session import project_require, get_db_by_session, get_project
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest
from setezor.database.models import Resource, Resource_Software, Software, \
    Vulnerability_Resource_Soft, \
    Vulnerability, VulnerabilityLink


class ResourceView(BaseView):
    endpoint = '/resource'
    queries_path = 'resource'

    @BaseView.route('POST', '/{id}/vulnerabilities')
    @project_require
    async def create(self, request: PMRequest) -> Response:
        resource_id = int(request.match_info.get('id'))
        db = await get_db_by_session(request=request)
        body = await request.json()
        if software_id := body.pop("software_id"):
            software = db.software.get_by_id(id=int(software_id))
        else:
            software = db.software.create()
        resource_software = db.resource_software.get_or_create_by_ids(**{
            "resource_id": resource_id,
            "software_id": software.id
        })
        vulnerability = db.vulnerability.get_or_create(**body)
        db.vuln_res_soft.get_or_create(**{
            "vulnerability_id": vulnerability.id,
            "resource_soft_id": resource_software.id,
            "confirmed": True
        })
        return json_response(status=201)

    @BaseView.route('GET', '/{id}/vulnerabilities')
    @project_require
    async def get_resource_vulnerabilities(self, request: PMRequest):
        resource_id = int(request.match_info.get('id'))
        db = await get_db_by_session(request=request)
        session = db.db.create_session()
        res = session.query(Resource, Resource_Software, Software, Vulnerability_Resource_Soft, Vulnerability, VulnerabilityLink).\
            join(Resource_Software, Resource.id == Resource_Software.resource_id).\
            join(Software, Resource_Software.software_id == Software.id).\
            join(Vulnerability_Resource_Soft, Resource_Software.id == Vulnerability_Resource_Soft.resource_soft_id, isouter=True).\
            join(Vulnerability, Vulnerability_Resource_Soft.vulnerability_id == Vulnerability.id, isouter=True).\
            join(VulnerabilityLink, Vulnerability.id == VulnerabilityLink.vulnerability_id, isouter=True).\
            filter(Resource.id == resource_id).all()
        result = {}
        resource = {}
        if res:
            resource = {
                "ip": res[0].Resource._ip_id.ip if res[0].Resource.ip_id else "",
                "domain": res[0].Resource._domain_id.domain if res[0].Resource.domain_id else "",
                "port": res[0].Resource._port_id.port if res[0].Resource.port_id else ""
            }
        for obj in res:
            if not obj.Vulnerability_Resource_Soft:
                continue
            vuln_res_soft_id = obj.Vulnerability_Resource_Soft.id
            screenshots_count = len(
                obj.Vulnerability_Resource_Soft._screenshot)
            if not result.get(vuln_res_soft_id):
                result.update({
                    vuln_res_soft_id: {
                        "vuln_res_soft_id": obj.Vulnerability_Resource_Soft.id,
                        "vendor": obj.Software.vendor,
                        "product": obj.Software.product,
                        "type": obj.Software.type,
                        "version": obj.Software.version,
                        "build": obj.Software.build,
                        "patch": obj.Software.patch,
                        "platform": obj.Software.platform,
                        "name": obj.Vulnerability.name,
                        "cve": obj.Vulnerability.cve,
                        "cwe": obj.Vulnerability.cwe,
                        "confirmed": obj.Vulnerability_Resource_Soft.confirmed,
                        "screenshots_count": screenshots_count,
                        "links": [obj.VulnerabilityLink.link] if obj.VulnerabilityLink else []
                    }
                })
            elif lnk := obj.VulnerabilityLink:
                result[vuln_res_soft_id]["links"].append(lnk.link)
        return json_response(status=200, data={"resource": resource, "vulns": list(result.values())})
