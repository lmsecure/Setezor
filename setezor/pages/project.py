
from typing import Annotated
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, Request
from setezor.dependencies.project import get_user_id
from setezor.services import UserProjectService
from setezor.services.analytics_service import AnalyticsService
from setezor.services.user_service import UsersService
from setezor.services.scan_service import ScanService
from .import TEMPLATES_DIR

router = APIRouter(tags=["Pages"])


@router.get("/projects")
async def projects_page(
    request: Request,
    users_service:  Annotated[UsersService, Depends(UsersService.new_instance)],
    user_project_service: Annotated[UserProjectService, Depends(UserProjectService.new_instance)],
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    scans_service: Annotated[ScanService, Depends(ScanService.new_instance)],
    user_id: str = Depends(get_user_id),
):
    """Формирует html страницу выбора проекта на основе jinja2 шаблона и возвращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    projects = await user_project_service.get_user_projects(user_id=user_id)
    user = await users_service.get(user_id=user_id)

    owned_projects = []
    shared_projects = []
    for project_obj, role, owner_login in projects:
        scans = await scans_service.list(project_obj.id)
        scan_ids = [scan.id for scan in scans]
        analytics = {
            "top_ports": await analytics_service.get_top_ports(project_obj.id, scan_ids),
            "top_protocols": await analytics_service.get_top_protocols(project_obj.id, scan_ids),
            "top_products": await analytics_service.get_top_products(project_obj.id, scan_ids),
            "device_types": await analytics_service.get_device_types(scan_ids, project_obj.id),
            "ip_count" : await analytics_service.get_ip_count(scan_ids, project_obj.id),
            "port_count" : await analytics_service.get_port_count(scan_ids, project_obj.id)
        }

        analytics['top_ports'] = {
            'labels': [i[0] for i in analytics["top_ports"]],
            'data': [i[1] for i in analytics["top_ports"]],
        }
        analytics['top_protocols'] = {
            'labels': [i[0] for i in analytics["top_protocols"]],
            'data': [i[1] for i in analytics["top_protocols"]],
        }
        analytics['top_products'] = {
            'labels': [i[0] for i in analytics["top_products"]],
            'data': [i[1] for i in analytics["top_products"]],
        }
        item = {
            "project": project_obj,
            "role": role,
            "owner_login": owner_login,
            "analytics": analytics
        }

        if role and role.lower() == 'owner':
            owned_projects.append(item)
        else:
            shared_projects.append(item)

    return TEMPLATES_DIR.TemplateResponse(
        name="projects/base_project.html",
        context={
            "request": request,
            "user_id": user.id,
            "is_superuser": user.is_superuser,
            "owned_projects": owned_projects,
            "shared_projects": shared_projects,
        }
    )