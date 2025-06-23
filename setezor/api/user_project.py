from typing import Annotated
from fastapi import APIRouter, Depends

from setezor.dependencies.project import get_current_project, get_user_id, role_required
from setezor.schemas.roles import Roles
from setezor.schemas.user_project import UserChangeRoleInProjectForm
from setezor.services.user_project_service import UserProjectService


router = APIRouter(prefix="/user_project", tags=["UserProject"])


@router.get("")
async def list_user_in_project(
    user_project_service: Annotated[UserProjectService, Depends(UserProjectService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required([Roles.owner]))
) -> list:
    return await user_project_service.list_users_in_project(user_id=user_id,
                                                          project_id=project_id)


@router.patch("/change_role")
async def change_user_role_in_project(
    user_project_service: Annotated[UserProjectService, Depends(UserProjectService.new_instance)],
    change_user_role_form: UserChangeRoleInProjectForm,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner]))
):
    return await user_project_service.change_user_role_in_project(project_id=project_id,
                                                                change_user_role_form=change_user_role_form)