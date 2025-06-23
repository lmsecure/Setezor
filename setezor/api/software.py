
from typing import Annotated
from fastapi import APIRouter, Depends
from setezor.dependencies.project import get_current_project, role_required
from setezor.services import SoftwareService
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/software",
    tags=["Software"],
)

@router.get("")
async def list_softwares(
    software_service: Annotated[SoftwareService, Depends(SoftwareService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await software_service.list()
