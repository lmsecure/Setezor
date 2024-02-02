from aiohttp.web import Request, Response
from app_routes.session import project_require, get_db_by_session
from app_routes.api.base_web_view import BaseView
from modules.export.xlsx import XLSXReport
from database.queries_files.base_queries import BaseQueries


class ReportsView(BaseView):
    endpoint = '/reports'

    @BaseView.route('GET', '/xlsx')
    @project_require
    async def download_xlsx_report(self, request: Request) -> Response:
        db = await get_db_by_session(request=request)
        report_maker = XLSXReport()
        data = {k: v.get_all() for k, v in db.__dict__.items() if v and isinstance(v, BaseQueries)}
        report = report_maker.generate_report(data)
        return Response(body=report.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')