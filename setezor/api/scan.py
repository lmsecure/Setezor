
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_current_scan_id, get_user_id, role_required
from setezor.models.scan import Scan
from setezor.schemas.scan import ScanCreateForm, ScanPickForm
from setezor.services.auth_service import AuthService
from setezor.services.scan_service import ScanService
from setezor.schemas.roles import Roles

router = APIRouter(
    prefix="/scan",
    tags=["Scan"],
)

@router.get("")
async def get_scans(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
)-> list[Scan]:
    return await ScanService.list(uow=uow, project_id=project_id)


@router.get("/current")
async def get_picked_scan(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    scan_id: str = Depends(get_current_scan_id),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> Scan:
    return await ScanService.get(uow=uow, id=scan_id, project_id=project_id)