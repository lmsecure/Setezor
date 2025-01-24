import json
import uuid
from setezor.pages import TEMPLATES_DIR
from setezor.services import ObjectTypeService
from setezor.managers import ProjectManager
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project
from setezor.modules.wappalyzer.wappalyzer import WappalyzerParser
from fastapi import APIRouter, Request, Depends
from setezor.services.analytics_service import AnalyticsService
from setezor.tools.ip_tools import get_interfaces
import pprint

router = APIRouter(tags=["Info"])


@router.get('/info/')
async def info_page(
    request: Request,
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
):
    """Формирует html страницу отображения информации из базы на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    project = await ProjectManager.get_by_id(uow=uow, project_id=project_id)
    analytics = await AnalyticsService.get_whois_data(uow=uow, project_id=project_id)
    l7_software_columns = AnalyticsService.get_l7_software_columns_tabulator_data()
    l4_software_columns = AnalyticsService.get_l4_software_columns_tabulator_data()
    ip_mac_port_columns = AnalyticsService.get_ip_mac_port_columns_tabulator_data()
    domain_ip_columns = AnalyticsService.get_domain_ip_columns_tabulator_data()
    soft_vuln_link_columns = AnalyticsService.get_soft_vuln_link_columns_tabulator_data()
    ip_columns = AnalyticsService.get_ip_columns_tabulator_data()
    mac_columns = AnalyticsService.get_mac_columns_tabulator_data()
    port_columns = AnalyticsService.get_port_columns_tabulator_data()
    return TEMPLATES_DIR.TemplateResponse(
        "info_tables.html",
        {"request": request,
         "analytics": analytics,
         "project": project,
         "current_project": project.name,
         "current_project_id": project.id,
         'tabs': [
             {
                 'name': 'l7_software',
                 'is_hide': False,
                 'base_url': '/api/v1/analytics/l7_software',
                 'columns': l7_software_columns
             },
             {
                 'name': 'l4_software',
                 'is_hide': False,
                 'base_url': '/api/v1/analytics/l4_software',
                 'columns': l4_software_columns
             },
                         {
                'name': 'ip_mac_port',
                'is_hide': False,
                'base_url': '/api/v1/analytics/ip_mac_port',
                'columns': ip_mac_port_columns
            },
                         {
                'name': 'domain_ip',
                'is_hide': False,
                'base_url': '/api/v1/analytics/domain_ip',
                'columns': domain_ip_columns
            },
                         {
                'name': 'l7_soft_vuln_link',
                'is_hide': False,
                'base_url': '/api/v1/analytics/l7_soft_vuln_link',
                'columns': soft_vuln_link_columns
            },
                         {
                'name': 'l4_soft_vuln_link',
                'is_hide': False,
                'base_url': '/api/v1/analytics/l4_soft_vuln_link',
                'columns': soft_vuln_link_columns
            },
         ]})
