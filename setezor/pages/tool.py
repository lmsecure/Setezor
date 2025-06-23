from typing import Annotated
from setezor.pages import TEMPLATES_DIR
from setezor.services import ObjectTypeService
from setezor.services.project_service import ProjectService
from setezor.services.user_service import UsersService
from setezor.tools.acunetix import acunetix_groups_context, acunetix_targets_context, \
    acunetix_scans_context, acunetix_reports_context
from setezor.dependencies.project import get_current_project, get_user_id, get_user_role_in_project, role_required
from fastapi import APIRouter, Request, Depends
from setezor.schemas.roles import Roles


router = APIRouter(tags=["Tools"])


@router.get("/tools")
async def network_page(
    request: Request,
    object_type_service: Annotated[ObjectTypeService, Depends(ObjectTypeService.new_instance)],
    project_service: Annotated[ProjectService, Depends(ProjectService.new_instance)],
    user_service: Annotated[UsersService, Depends(UsersService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    role_in_project: Roles = Depends(get_user_role_in_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    """Формирует html страницу отображения топологии сети на основе jinja2 шаблона и возвращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    # is_scapy_running = project.schedulers.get('scapy').active_count
    device_types = [{'label': i.name.capitalize(), 'value': i.name} for i in (await object_type_service.list())]
    project = await project_service.get_by_id(project_id=project_id)
    user = await user_service.get(user_id=user_id)
    context = {"request": request,
               "project": project,
               'device_types': device_types,
               "role": role_in_project,
               "is_superuser": user.is_superuser,
               "user_id": user_id,
               'is_scapy_running': False,
               'current_project': project.name,
               'current_project_id': project.id}

    context.update(acunetix_groups_context())
    context.update(acunetix_targets_context())
    context.update(acunetix_scans_context())
    # context.update(await acunetix_reports_context(project.configs.files.acunetix_configs))
    context.update(await acunetix_reports_context())
    return TEMPLATES_DIR.TemplateResponse(name="network/tool_base.html", context=context)
