from fastapi import APIRouter, Depends, Response
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, role_required, get_current_scan_id
from setezor.services import PortService
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/l4",
    tags=["Resource"],
)


@router.get("")
async def list_resources(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[dict]:
    return await PortService.get_resources(uow=uow, project_id=project_id)


@router.get("/{l4_id}/vulnerabilities")
async def list_resource_vulnerabilities(
    uow: UOWDep,
    l4_id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await PortService.list_vulnerabilities(uow=uow, l4_id=l4_id, project_id=project_id)

@router.post("/{l4_id}/vulnerabilities")
async def add_resource_vulnerability(
    uow: UOWDep,
    l4_id: str,
    data: dict,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    await PortService.add_vulnerability(uow=uow, project_id=project_id, id=l4_id, data=data)
    return Response(status_code=201)

@router.get("/get_resources_for_snmp")
async def get_resources_for_snmp(
    uow: UOWDep,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project)
) -> list:
    return await PortService.get_resources_for_snmp(uow=uow, project_id=project_id, scan_id=scan_id)
