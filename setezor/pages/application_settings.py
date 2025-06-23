from typing import Annotated
from fastapi import APIRouter, Depends, Request
from setezor.dependencies.project import get_current_project, get_user_id, get_user_role_in_project, role_required
from setezor.services.project_service import ProjectService
from setezor.services.user_service import UsersService
from .import TEMPLATES_DIR
from setezor.schemas.roles import Roles


router = APIRouter(tags=["Pages"])

@router.get('/application_settings')
async def settings_page(
    request: Request,
    project_service: Annotated[ProjectService, Depends(ProjectService.new_instance)],
    users_service: Annotated[UsersService, Depends(UsersService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    role_in_project: Roles = Depends(get_user_role_in_project),
    _: bool = Depends(role_required([Roles.owner]))
):
    """Формирует html страницу отображения топологии сети на основе jinja2 шаблона и возвращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    project = await project_service.get_by_id(project_id=project_id)
    user = await users_service.get(user_id=user_id)
    context = {
        "request": request,
        "project": project,
        "is_superuser": user.is_superuser,
        'current_project': project.name,
        'current_project_id': project.id,
        "role": role_in_project,
        'tab': {'name': "Agents",
                'base_url': f'/api/v1/agents/settings',
                'columns': []
                }
    }
    return TEMPLATES_DIR.TemplateResponse(name="settings/application_settings.html", context=context)