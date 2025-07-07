from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Response
from setezor.dependencies.project import get_current_project, role_required
from setezor.services import AcunetixService
from setezor.schemas.acunetix.schemes.group import GroupForm, GroupMembershipSet, GroupTargetProxy
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/groups"
)

@router.get("")
async def get_acunetix_groups(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    groups = await acunetix_service.get_groups(project_id=project_id, acunetix_id=acunetix_id)
    return groups


@router.post("")
async def add_group(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    group_add_form: GroupForm, 
    acunetix_id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status, msg = await acunetix_service.add_group(project_id=project_id, acunetix_id=acunetix_id, form=group_add_form)
    return Response(content=msg, status_code=status)


@router.get("/{group_id}/targets")
async def get_group_targets(
    group_id: str,
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    acunetix_id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    group_targets = await acunetix_service.get_group_targets(group_id=group_id, project_id=project_id, acunetix_id=acunetix_id)
    return group_targets

@router.put("/{group_id}/targets")
async def get_group_targets(
    group_id: str,
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    acunetix_id: str,
    payload: GroupMembershipSet,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await acunetix_service.set_group_targets(group_id=group_id, project_id=project_id, acunetix_id=acunetix_id, payload=payload)
    return Response(status_code=status)

@router.put("/{group_id}/proxy")
async def set_group_targets_proxy(
    group_id: str,
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    acunetix_id: str,
    payload: dict,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status = await acunetix_service.set_group_targets_proxy(group_id=group_id, project_id=project_id, acunetix_id=acunetix_id, payload=payload)
    return Response(status_code=status)