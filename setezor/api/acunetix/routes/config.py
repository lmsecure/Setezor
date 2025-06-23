
from fastapi import APIRouter, Depends
from setezor.dependencies import get_current_project
from setezor.dependencies.project import role_required
from setezor.models import Acunetix
from setezor.services import AcunetixService
from setezor.db.uow_dependency import UOWDep
from setezor.schemas.roles import Roles


router = APIRouter(prefix="/config")


@router.get("")
async def get_apis(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[Acunetix]:
    apis: list[Acunetix] = await AcunetixService.get_project_apis(uow=uow, project_id=project_id)
    return apis


@router.post("")
async def add_config(
    uow: UOWDep,
    config: Acunetix,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    new_config = await AcunetixService.add_config(uow=uow, project_id=project_id, config=config)
    return True