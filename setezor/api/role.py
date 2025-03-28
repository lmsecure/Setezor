from fastapi import APIRouter, Depends

from setezor.dependencies.project import get_current_project, role_required
from setezor.dependencies.uow_dependency import UOWDep
from setezor.models.role import Role
from setezor.schemas.roles import Roles
from setezor.services.role_service import RoleService



router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("")
async def get_roles_list(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner]))
) -> list[Role]:
    return await RoleService.list(uow=uow)