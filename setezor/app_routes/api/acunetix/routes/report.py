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
            params.update({"s": f"created:{sort[0]['dir']}"})
        reports, count = await Report.get_all(params=params,credentials=credentials)
        if not count % size:
            last_page = count // size
        else:
            last_page = count // size + 1
        return json_response(status=200, data={"data": reports, "last_page": last_page})

    @BaseView.route('POST', '/reports/')
    @project_require
    async def create_report(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)
        payload = await request.json()
        status, msg = await Report.create(payload=payload, credentials=credentials)
        return json_response(status=status, data=msg)

    @BaseView.route('GET', '/reports/{report_id}/download/')
    @project_require
    async def download_report(self, request: PMRequest) -> Response:
        project = await get_project(request=request)
        credentials = await Config.get(project.configs.files.acunetix_configs)
        if not credentials:
            return json_response(status=500)

        if not (query := request.rel_url.query):
            return json_response(status=400, data={"error": "Missing query params"})

        if not (extension := query.get("format")) in ("pdf", "html"):
            return json_response(status=400, data={"error": "Wrong file extension. Expected pdf or html"})

        report_id = request.match_info['report_id']

        filename, data, status = await Report.download(id=report_id, extension=extension, credentials=credentials)

        if status != 200:
            return json_response(status=status,data={"error":"Report is not ready"})

        if extension == "pdf":
            content_type = "application/pdf"
        else:
            content_type = "text/html"

        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        return Response(body=data, headers=headers, content_type=content_type)


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
