
from fastapi import APIRouter, Depends
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project
from setezor.services import SoftwareService

router = APIRouter(
    prefix="/software",
    tags=["Software"],
)

@router.get("")
async def list_softwares(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
):
    return await SoftwareService.list(uow=uow)
