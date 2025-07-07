from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Response
from setezor.schemas.acunetix.schemes.scan import GroupScanStart, ScanWithInterval, TargetScanStart
from setezor.dependencies.project import get_current_project, get_current_scan_id, role_required
from setezor.services import AcunetixService
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/scans"
)

@router.get("")
async def get_acunetix_scans(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await acunetix_service.get_scans(project_id=project_id, acunetix_id=acunetix_id)

@router.post("")
async def create_scan(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    scan_form: TargetScanStart | GroupScanStart, 
    acunetix_id: Optional[str] = None,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await acunetix_service.create_scan(project_id=project_id, acunetix_id=acunetix_id, scan_id=scan_id, form=scan_form)
    return Response(status_code=201)  


@router.get("/speeds")
async def get_scans_speeds(
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return AcunetixService.get_scans_speeds()

@router.get("/profiles")
async def get_scanning_profiles(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await acunetix_service.get_scanning_profiles(project_id=project_id)