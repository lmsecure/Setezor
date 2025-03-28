
from setezor.models.role import Role
from setezor.pages import TEMPLATES_DIR
from setezor.managers import ProjectManager
from setezor.services.user_service import UsersService
from setezor.tools.acunetix import acunetix_groups_context, acunetix_targets_context, \
    acunetix_scans_context, acunetix_reports_context
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_user_id, get_user_role_in_project, role_required
from fastapi import APIRouter, Request, Depends
from setezor.schemas.roles import Roles


router = APIRouter(tags=["Vulnerabilities"])

@router.get("/vulnerabilities")
async def vulnerabilities_page(
    request: Request,
    uow: UOWDep,
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
    project = await ProjectManager.get_by_id(uow=uow, project_id=project_id)
    project_name = project.name
    project_id = project.id
    user = await UsersService.get(uow=uow, id=user_id)
    context = {
        "request":request,
        "is_superuser": user.is_superuser,
        "role": role_in_project,
        "user_id": user_id,
        "tabs": [
            {'name' : 'l4_resources',
             'base_url': 'l4',
             'columns': [
                {'field': 'id', 'title': 'ID'},
                {'field': 'ip', 'title': 'IP'},
                {'field': 'port', 'title': 'PORT'}]
            },
            {'name': 'l7_resources',
             'base_url': "l7",
             'columns': [
                {'field': 'id', 'title': 'ID'},
                {'field': 'ip', 'title': 'IP'},
                {'field': 'port', 'title': 'PORT'},
                {'field': 'domain', 'title': 'DOMAIN'}]
            }
        ],
        'current_project': project_name, 
        'current_project_id': project_id,
    }
    return TEMPLATES_DIR.TemplateResponse(name="vulnerabilities.html", context=context)
