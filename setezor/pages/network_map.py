from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, Request
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_user_id, get_user_role_in_project, role_required
from setezor.models.role import Role
from setezor.services import UserProjectService
from setezor.managers import ProjectManager
from setezor.services.user_service import UsersService
from setezor.services.object_type_service import ObjectTypeService
from .import TEMPLATES_DIR


router = APIRouter(tags=["Pages"])

@router.get('/network-map')
async def network_page(
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
    device_types = [{"value" : obj.id, "label" : obj.name} for obj in await ObjectTypeService.list(uow=uow)]
    context={"request": request,
            "project": project,
            "is_superuser": user.is_superuser,
            "role": role_in_project,
            "current_project": project.name,
            "current_project_id": project.id,
            "device_types": device_types}
    return TEMPLATES_DIR.TemplateResponse(name="network/map_and_info.html", context=context
                                           )