from fastapi import APIRouter, Depends

from setezor.dependencies.project import get_current_project, get_user_id, role_required
from setezor.dependencies.uow_dependency import UOWDep
from setezor.schemas.roles import Roles
from setezor.schemas.user_project import UserChangeRoleInProjectForm
from setezor.services.user_project_service import UserProjectService


router = APIRouter(prefix="/user_project", tags=["UserProject"])


@router.get("")
async def list_user_in_project(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required([Roles.owner]))
) -> list:
    return await UserProjectService.list_users_in_project(uow=uow, user_id=user_id,
                                                          project_id=project_id)


@router.patch("/change_role")
async def change_user_role_in_project(
    uow: UOWDep,
    change_user_role_form: UserChangeRoleInProjectForm,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner]))
):
    return await UserProjectService.change_user_role_in_project(uow=uow, project_id=project_id,
                                                                change_user_role_form=change_user_role_form)