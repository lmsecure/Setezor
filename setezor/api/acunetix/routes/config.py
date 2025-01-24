
from fastapi import APIRouter, Depends
from setezor.dependencies import get_current_project
from setezor.models import Acunetix
from setezor.services import AcunetixService
from setezor.api.dependencies import UOWDep


router = APIRouter(prefix="/config")


@router.get("")
async def get_apis(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
) -> list[Acunetix]:
    apis: list[Acunetix] = await AcunetixService.get_project_apis(uow=uow, project_id=project_id)
    return apis


@router.post("")
async def add_config(
    uow: UOWDep,
    config: Acunetix,
    project_id: str = Depends(get_current_project),
):
    new_config = await AcunetixService.add_config(uow=uow, project_id=project_id, config=config)
    return True