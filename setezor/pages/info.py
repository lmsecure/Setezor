from typing import Annotated
from setezor.pages import TEMPLATES_DIR
from setezor.dependencies.project import get_current_project, get_user_id, get_user_role_in_project, role_required
from fastapi import APIRouter, Request, Depends
from setezor.services.project_service import ProjectService
from setezor.services.user_service import UsersService
from setezor.schemas.roles import Roles

router = APIRouter(tags=["Info"])


@router.get('/info')
async def info_page(
    request: Request,
    project_service: Annotated[ProjectService, Depends(ProjectService.new_instance)],
    users_service: Annotated[UsersService, Depends(UsersService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    role_in_project: Roles = Depends(get_user_role_in_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    project = await project_service.get_by_id(project_id=project_id)
    user = await users_service.get(user_id=user_id)
    context = {
        "request": request,
        "project": project,
        "current_project": project.name,
        "current_project_id": project.id,
        "is_superuser": user.is_superuser,
        "user_id": user_id,
        "role": role_in_project,
    }
    return TEMPLATES_DIR.TemplateResponse("info_tables.html", context=context)