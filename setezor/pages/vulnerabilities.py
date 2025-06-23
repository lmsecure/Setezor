
from typing import Annotated
from setezor.pages import TEMPLATES_DIR
from setezor.services.project_service import ProjectService
from setezor.services.user_service import UsersService
from setezor.dependencies.project import get_current_project, get_user_id, get_user_role_in_project, role_required
from fastapi import APIRouter, Request, Depends
from setezor.schemas.roles import Roles


router = APIRouter(tags=["Vulnerabilities"])

@router.get("/vulnerabilities")
async def vulnerabilities_page(
    request: Request,
    project_service: Annotated[ProjectService, Depends(ProjectService.new_instance)],
    users_service: Annotated[UsersService, Depends(UsersService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    role_in_project: Roles = Depends(get_user_role_in_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    """Формирует html страницу отображения информации из базы на основе jinja2 шаблона и возвращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    project = await project_service.get_by_id(project_id=project_id)
    project_name = project.name
    project_id = project.id
    user = await users_service.get(user_id=user_id)
    context = {
        "request":request,
        "is_superuser": user.is_superuser,
        "role": role_in_project,
        "user_id": user_id,
        "tab":
            {'name' : 'l4_resources',
             'base_url': 'l4',
             'columns': [
                {'field': 'id', 'title': 'ID'},
                {'field': 'ip', 'title': 'IP'},
                {'field': 'port', 'title': 'PORT'},
                {'field': 'domain', 'title': 'DOMAIN'}]
            },
        'current_project': project_name, 
        'current_project_id': project_id,
    }
    return TEMPLATES_DIR.TemplateResponse(name="vulnerabilities.html", context=context)
