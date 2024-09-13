import json
from setezor.app_routes.api.base_web_view import BaseView
from setezor.app_routes.session import get_project, project_require
from setezor.modules.application.pm_request import PMRequest
from setezor.modules.acunetix.acunetix_config import Config
from setezor.modules.acunetix.report import Report
from aiohttp.web import json_response, Response


class AcunetixReportView:
    @BaseView.route('GET', '/reports/')
    @project_require
    async def get_reports(self, request: PMRequest) -> Response:
        query = request.rel_url.query
        project = await get_project(request=request)
        reports = await project.acunetix_manager.get_reports(name=query.get("acunetix_name"))
        return json_response(status=200, data=reports)

    @BaseView.route('POST', '/reports/')
    @project_require
    async def create_report(self, request: PMRequest) -> Response:
        query = request.rel_url.query
        acunetix_name = query.get("acunetix_name")
        project = await get_project(request=request)
        payload = await request.json()
        status, msg = await project.acunetix_manager.create_report(name=acunetix_name, payload=payload)
        return json_response(status=status, data=msg)

    @BaseView.route('GET', '/reports/{report_id}/download/')
    @project_require
    async def download_report(self, request: PMRequest) -> Response:
        query = request.rel_url.query
        project = await get_project(request=request)
        if not (query := request.rel_url.query):
            return json_response(status=400, data={"error": "Missing query params"})

        if not (extension := query.get("format")) in ("pdf", "html"):
            return json_response(status=400, data={"error": "Wrong file extension. Expected pdf or html"})
        report_id = request.match_info['report_id']
        filename, data, status = await project.acunetix_manager.get_report_file(name=query.get("acunetix_name"),
                                                                report_id=report_id,
                                                                extension=extension)
        if status != 200:
            return json_response(status=status, data={"error": "Report is not ready"})
        if extension == "pdf":
            content_type = "application/pdf"
        else:
            content_type = "text/html"
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        return Response(body=data, headers=headers, content_type=content_type)

    @BaseView.route('GET', '/reports/templates/')
    @project_require
    async def report_templates(self, request: PMRequest):
        project = await get_project(request)
        templates = await project.acunetix_manager.get_report_templates()
        return json_response(status=200, data=templates)


'''

@router.get("/templates")
async def get_report_templates() -> list[ReportTemplate]:
    result = await send_request(url="/api/v1/report_templates", method="GET")
    return result["templates"]


@router.get("/")
async def get_reports_by_date(date: datetime.date) -> list[Report]:
    limit = 100
    prev_day = date - datetime.timedelta(days=1)
    next_day = date + datetime.timedelta(days=1)
    params = {
        "l": limit,
        "s": "created:desc",
        #"q": f"created:>={prev_day}T19:00:00.000Z;created:<={next_day}T19:00:00.000Z;"
    }
    raw_data = await send_request(url="/api/v1/reports", method="GET", params=params)

    reports: list[Report] = []
    for report in raw_data.get("reports"):
        reports.append(Report(**report))
    return reports


@router.get("/{report_id}/pdf")
async def get_pdf_report(report_id: str):
    report = await send_request(url=f"/api/v1/reports/{report_id}", method="GET")
    download_link = ""
    for link in report.get("download"):
        if link.endswith(".pdf"):
            download_link = link
            break
    filename, data = await send_request(url=download_link, method="GET")
    headers = {'Content-Disposition': f'attachment; filename="{filename}"',"content-type": "application/octet-stream"}
    return Response(data, headers=headers, media_type='application/pdf')

'''
