
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, Request
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_user_id
from setezor.services import UserProjectService
from setezor.services.analytics_service import AnalyticsService
from setezor.services.user_service import UsersService
from .import TEMPLATES_DIR
import pprint

router = APIRouter(tags=["Pages"])


@router.get("/projects")
async def projects_page(
    request: Request,
    uow: UOWDep,
    user_id: str = Depends(get_user_id),
):
    """Формирует html страницу выбора проекта на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    projects = await UserProjectService.get_user_projects(uow=uow, user_id=user_id)
    user = await UsersService.get(uow=uow, id=user_id)

    result = []

    for project_obj in projects:
        analytics = {
            "top_ports": await AnalyticsService.get_top_ports(uow, project_obj.id),
            "top_protocols": await AnalyticsService.get_top_protocols(uow, project_obj.id),
            "top_products": await AnalyticsService.get_top_products(uow, project_obj.id),
            "device_types": await AnalyticsService.get_device_types(uow, project_obj.id),
            "ip_count" : await AnalyticsService.get_ip_count(uow, project_obj.id),
            "port_count" : await AnalyticsService.get_port_count(uow, project_obj.id)
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

        result.append({
            "project": project_obj,
            "analytics": analytics
        })

    return TEMPLATES_DIR.TemplateResponse(
        name="projects/base_project.html",
        context={
            "request": request,
            "is_superuser": user.is_superuser,
            "projects": result
        }
    )