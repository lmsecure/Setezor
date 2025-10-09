from typing import Annotated, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Response, UploadFile
from setezor.schemas.acunetix.schemes.target import SyncPayload, TargetToSync
from setezor.dependencies.project import get_current_project, get_current_scan_id, role_required
from setezor.services import AcunetixService
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/targets"
)

@router.get("")
async def get_all_targets(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await acunetix_service.get_targets(acunetix_id=acunetix_id, project_id=project_id)

@router.get("/sync")
async def get_all_targets_for_sync(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    scope_id: str,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    return await acunetix_service.get_targets_for_sync(acunetix_id=acunetix_id, project_id=project_id, scope_id=scope_id)

@router.post("/sync")
async def sync_targets_between_setezor_and_acunetix(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    sync_payload: SyncPayload,
    background_tasks: BackgroundTasks,
    project_id: str = Depends(get_current_project),
    scan_id: str = Depends(get_current_scan_id),
    _: bool = Depends(role_required([Roles.owner, Roles.executor])),
):
    background_tasks.add_task(acunetix_service.sync_targets_between_setezor_and_acunetix, sync_payload=sync_payload, scope_id=sync_payload.scope_id, scan_id=scan_id, project_id=project_id)
    return None



@router.post("")
async def add_targets(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    payload: dict,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    return await acunetix_service.add_targets(acunetix_id=acunetix_id, project_id=project_id, payload=payload)

@router.post("/import_csv")
async def import_targets_from_csv(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    group_id: Annotated[str, Form()], 
    targets_csv: UploadFile = File(),
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await acunetix_service.import_targets_from_csv(acunetix_id=acunetix_id, 
                                                         project_id=project_id, group_id=group_id, 
                                                         targets_csv=targets_csv)
    return Response(status_code=status)  

@router.delete("/{target_id}")
async def delete_target(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    target_id: str,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status, msg = await acunetix_service.delete_target(acunetix_id=acunetix_id, project_id=project_id, target_id=target_id)
    return Response(status_code=status) 

@router.put("/{target_id}/proxy")
async def set_target_proxy(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    target_id:str,
    payload: dict,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await acunetix_service.set_target_proxy(acunetix_id=acunetix_id, target_id=target_id, project_id=project_id, payload=payload)
    return Response(status_code=status) 

@router.put("/{target_id}/cookies")
async def set_target_cookies(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    target_id:str,
    payload: dict,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await acunetix_service.set_target_cookies(acunetix_id=acunetix_id, target_id=target_id, project_id=project_id, payload=payload)
    return Response(status_code=status) 

@router.put("/{target_id}/headers")
async def set_target_headers(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    target_id:str,
    payload: dict,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await acunetix_service.set_target_headers(acunetix_id=acunetix_id, target_id=target_id, project_id=project_id, payload=payload)
    return Response(status_code=status) 