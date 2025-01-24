from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, Request
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project
from setezor.services import UserProjectService
from setezor.managers import ProjectManager
from setezor.services.analytics_service import AnalyticsService
from .import TEMPLATES_DIR


router = APIRouter(tags=["Pages"])

@router.get('/projects_dashboard')
async def projects_dashboard_page(
    request: Request,
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
):
    """Формирует html страницу отображения топологии сети на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    project = await ProjectManager.get_by_id(uow=uow, project_id=project_id)
    analytics = await AnalyticsService.get_all_analytics(uow=uow, project_id=project_id)
    columns = AnalyticsService.get_l4_software_columns_tabulator_data()
    return TEMPLATES_DIR.TemplateResponse(
        "projects_dashboard.html",
        {"request": request,
        "analytics": analytics,
        "project": project,
        "current_project": project.name,
        "current_project_id": project.id,
                        'tab': {f'name': 'analytics',
                    'base_url': f'/api/v1/analytics/l4_software',
                    'columns': columns}})