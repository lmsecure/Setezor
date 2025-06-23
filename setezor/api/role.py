from typing import Annotated
from fastapi import APIRouter, Depends

from setezor.dependencies.project import get_current_project, role_required
from setezor.models.role import Role
from setezor.schemas.roles import Roles
from setezor.services.role_service import RoleService



router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("")
async def get_roles_list(
    role_service: Annotated[RoleService, Depends(RoleService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner]))
) -> list[Role]:
    return await role_service.list()