from fastapi import APIRouter, Depends, Request
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project
from setezor.services import UserProjectService
from setezor.managers import ProjectManager
from .import TEMPLATES_DIR


router = APIRouter(tags=["Pages"])

@router.get('/scopes')
async def scopes_page(
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
    context = {
        "request": request,
        "project": project,
        'current_project': project.name,
        'current_project_id': project.id,
    }
    return TEMPLATES_DIR.TemplateResponse(name="scopes.html", context=context)