
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, Request
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project, get_user_id
from setezor.services import UserProjectService
from setezor.services.analytics_service import AnalyticsService
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
    analytics_lst = []
    result = []
    for project_obj in projects:
        analytics = await AnalyticsService.get_all_analytics(uow=uow, project_id=project_obj.id)
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
        project_obj.id = project_obj.id
        result.append({"project" : project_obj, "analytics" : analytics})
    return TEMPLATES_DIR.TemplateResponse(name="projects/base_project.html", context={"request": request,
                                                                                      "projects": result})