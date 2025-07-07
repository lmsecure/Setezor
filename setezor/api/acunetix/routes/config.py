
from typing import Annotated
from fastapi import APIRouter, Depends
from setezor.dependencies import get_current_project
from setezor.dependencies.project import role_required
from setezor.models import Acunetix
from setezor.services import AcunetixService
from setezor.schemas.roles import Roles
from setezor.unit_of_work.unit_of_work import UnitOfWork


router = APIRouter(prefix="/config")


@router.get("")
async def get_apis(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[Acunetix]:
    apis: list[Acunetix] = await acunetix_service.get_project_apis(project_id=project_id)
    return apis


@router.post("")
async def add_config(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    config: Acunetix,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    new_config = await acunetix_service.add_config(project_id=project_id, config=config)
    return True