import csv
from io import StringIO
import json

from aiohttp.web import Response

from setezor.app_routes.session import project_require, get_db_by_session
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.export.xlsx import XLSXReport
from setezor.database.queries_files.base_queries import BaseQueries
from setezor.modules.application import PMRequest

class ReportsView(BaseView):
    endpoint = '/reports'

    @BaseView.route('GET', '/xlsx')
    @project_require
    async def download_xlsx_report(self, request: PMRequest) -> Response:
        db = await get_db_by_session(request=request)
        report_maker = XLSXReport()
        data = {k: v.get_all() for k, v in db.__dict__.items() if v and isinstance(v, BaseQueries)}
        report = report_maker.generate_report(data)
        return Response(body=report.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    
    @BaseView.route('GET', '/csv')
    @project_require
    async def download_csv_report(self, request: PMRequest) -> Response:
        db = await get_db_by_session(request=request)
        query = request.rel_url.query
        filters: dict = json.loads(query.get('filters'))
        rows = db.pivot.get_all(filters=filters, result_format=None)
        file = StringIO()
        writer = csv.writer(file)
        if rows:
            writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow(row.values())
        return Response(body=file.getvalue(), headers= {
            'Content-Type': 'text/csv; charset=UTF-8',
            'CONTENT-DISPOSITION': 'attachment;filename=ip_port.csv'
        })