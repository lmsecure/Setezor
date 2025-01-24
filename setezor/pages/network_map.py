from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, Request
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project
from setezor.services import UserProjectService
from setezor.managers import ProjectManager
from .import TEMPLATES_DIR


router = APIRouter(tags=["Pages"])

@router.get('/network-map')
async def network_page(
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
    return TEMPLATES_DIR.TemplateResponse(name="network/map_and_info.html",
                                           context={"request": request,
                                                    "project": project,
                                                    "current_project": project.name,
                                                    "current_project_id": project.id})