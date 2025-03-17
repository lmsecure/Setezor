from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, Request
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_user_id, get_user_role_in_project, role_required
from setezor.models.role import Role
from setezor.services import UserProjectService
from setezor.managers import ProjectManager
from setezor.services.analytics_service import AnalyticsService
from setezor.services.user_service import UsersService
from .import TEMPLATES_DIR


router = APIRouter(tags=["Pages"])

@router.get('/projects_dashboard')
async def projects_dashboard_page(
    request: Request,
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    role_in_project: Role = Depends(get_user_role_in_project),
    _: bool = Depends(role_required(["owner", "viewer"]))
):
    """Формирует html страницу отображения топологии сети на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    project = await ProjectManager.get_by_id(uow=uow, project_id=project_id)
    user = await UsersService.get(uow=uow, id=user_id)
    last_scan_id = await AnalyticsService.get_last_scan_id(uow=uow, project_id=project_id)

    context = {
        "request": request,
        "project": project,
        "role": role_in_project,
        "is_superuser": user.is_superuser,
        "current_project": project.name,
        "current_project_id": project.id,
        'tab': {
            'name': 'analytics',
            'base_url': f'/api/v1/analytics/l4_software',
            'columns': AnalyticsService.get_l4_software_columns_tabulator_data()
        },
        "analytics": {}
    }

    return TEMPLATES_DIR.TemplateResponse(
        "projects_dashboard.html", context=context
    )