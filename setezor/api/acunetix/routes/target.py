from typing import Annotated, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Response, UploadFile
from setezor.schemas.acunetix.schemes.target import SyncPayload, TargetToSync
from setezor.db.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_current_scan_id, role_required
from setezor.services import AcunetixService
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/targets"
)

@router.get("")
async def get_all_targets(
    uow: UOWDep,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await AcunetixService.get_targets(uow=uow, acunetix_id=acunetix_id, project_id=project_id)

@router.get("/sync")
async def get_all_targets_for_sync(
    uow: UOWDep,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    return await AcunetixService.get_targets_for_sync(uow=uow, acunetix_id=acunetix_id, project_id=project_id)

@router.post("/sync")
async def sync_targets_between_setezor_and_acunetix(
    uow: UOWDep,
    sync_payload: SyncPayload,
    background_tasks: BackgroundTasks,
    project_id: str = Depends(get_current_project),
    scan_id: str = Depends(get_current_scan_id),
    _: bool = Depends(role_required([Roles.owner, Roles.executor])),
):
    background_tasks.add_task(AcunetixService.sync_targets_between_setezor_and_acunetix, uow=uow, sync_payload=sync_payload, scan_id=scan_id, project_id=project_id)
    return None



@router.post("")
async def add_targets(
    uow: UOWDep,
    payload: dict,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    return await AcunetixService.add_targets(uow=uow, acunetix_id=acunetix_id, project_id=project_id, payload=payload)

@router.post("/import_csv")
async def import_targets_from_csv(
    uow: UOWDep,
    group_id: Annotated[str, Form()], 
    targets_csv: UploadFile = File(),
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await AcunetixService.import_targets_from_csv(uow=uow, acunetix_id=acunetix_id, 
                                                         project_id=project_id, group_id=group_id, 
                                                         targets_csv=targets_csv)
    return Response(status_code=status)  

@router.delete("/{target_id}")
async def delete_target(
    uow: UOWDep,
    target_id: str,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status, msg = await AcunetixService.delete_target(uow=uow, acunetix_id=acunetix_id, project_id=project_id, target_id=target_id)
    return Response(status_code=status) 

@router.put("/{target_id}/proxy")
async def set_target_proxy(
    uow: UOWDep,
    target_id:str,
    payload: dict,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await AcunetixService.set_target_proxy(uow=uow, acunetix_id=acunetix_id, target_id=target_id, project_id=project_id, payload=payload)
    return Response(status_code=status) 

@router.put("/{target_id}/cookies")
async def set_target_cookies(
    uow: UOWDep,
    target_id:str,
    payload: dict,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await AcunetixService.set_target_cookies(uow=uow, acunetix_id=acunetix_id, target_id=target_id, project_id=project_id, payload=payload)
    return Response(status_code=status) 

@router.put("/{target_id}/headers")
async def set_target_headers(
    uow: UOWDep,
    target_id:str,
    payload: dict,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await AcunetixService.set_target_headers(uow=uow, acunetix_id=acunetix_id, target_id=target_id, project_id=project_id, payload=payload)
    return Response(status_code=status) 