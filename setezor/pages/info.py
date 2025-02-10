import json
import uuid
from setezor.models.role import Role
from setezor.pages import TEMPLATES_DIR
from setezor.services import ObjectTypeService
from setezor.managers import ProjectManager
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_user_id, get_user_role_in_project, role_required
from fastapi import APIRouter, Request, Depends
from setezor.services.analytics_service import AnalyticsService
from setezor.services.role_service import RoleService
from setezor.services.user_project_service import UserProjectService
from setezor.services.user_service import UsersService
from setezor.tools.ip_tools import get_interfaces
import pprint

router = APIRouter(tags=["Info"])


@router.get('/info')
async def info_page(
    request: Request,
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    role_in_project: Role = Depends(get_user_role_in_project),
    _: bool = Depends(role_required(["owner", "viewer"]))
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
    user = await UsersService.get(uow=uow, id=user_id)
    context =  {"request": request,
                "analytics": analytics,
                "project": project,
                "current_project": project.name,
                "current_project_id": project.id,
                "is_superuser": user.is_superuser,
                "role": role_in_project,
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
         ]}
    return TEMPLATES_DIR.TemplateResponse(
        "info_tables.html", context=context
        )


