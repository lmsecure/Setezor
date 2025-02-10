
from fastapi import APIRouter, Depends
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, role_required
from setezor.services import SoftwareService

router = APIRouter(
    prefix="/software",
    tags=["Software"],
)

@router.get("")
async def list_softwares(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner", "viewer"]))
):
    return await SoftwareService.list(uow=uow)
