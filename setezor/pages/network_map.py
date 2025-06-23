from typing import Annotated
from fastapi import APIRouter, Depends, Request
from setezor.dependencies.project import get_current_project, get_user_id, get_user_role_in_project, role_required
from setezor.services.project_service import ProjectService
from setezor.services.user_service import UsersService
from setezor.services.object_type_service import ObjectTypeService
from .import TEMPLATES_DIR
from setezor.schemas.roles import Roles


router = APIRouter(tags=["Pages"])

@router.get('/network-map')
async def network_page(
    request: Request,
    project_service: Annotated[ProjectService, Depends(ProjectService.new_instance)],
    users_service: Annotated[UsersService, Depends(UsersService.new_instance)],
    object_type_service: Annotated[ObjectTypeService, Depends(ObjectTypeService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    role_in_project: Roles = Depends(get_user_role_in_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    """Формирует html страницу отображения топологии сети на основе jinja2 шаблона и возвращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    project = await project_service.get_by_id(project_id=project_id)
    user = await users_service.get(user_id=user_id)
    device_types = [{"value" : obj.id, "label" : obj.name} for obj in await object_type_service.list()]
    context={"request": request,
            "project": project,
            "is_superuser": user.is_superuser,
            "role": role_in_project,
            "user_id": user_id,
            "current_project": project.name,
            "current_project_id": project.id,
            "device_types": device_types}
    return TEMPLATES_DIR.TemplateResponse(name="network/map_and_info.html", context=context
                                           )