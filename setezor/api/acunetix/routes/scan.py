from typing import Optional
from fastapi import APIRouter, Depends, Response
from setezor.schemas.acunetix.schemes.scan import GroupScanStart, ScanWithInterval, TargetScanStart
from setezor.db.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_current_scan_id, role_required
from setezor.services import AcunetixService
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/scans"
)

@router.get("")
async def get_acunetix_scans(
    uow: UOWDep,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await AcunetixService.get_scans(uow=uow, project_id=project_id, acunetix_id=acunetix_id)

@router.post("")
async def create_scan(
    uow: UOWDep,
    scan_form: TargetScanStart | GroupScanStart, 
    acunetix_id: Optional[str] = None,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await AcunetixService.create_scan(uow=uow, project_id=project_id, acunetix_id=acunetix_id, scan_id=scan_id, form=scan_form)
    return Response(status_code=201)  


@router.get("/speeds")
async def get_scans_speeds(
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return AcunetixService.get_scans_speeds()

@router.get("/profiles")
async def get_scanning_profiles(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await AcunetixService.get_scanning_profiles(uow=uow, project_id=project_id)