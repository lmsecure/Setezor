from typing import Annotated
from fastapi import APIRouter, Depends, Response
from setezor.dependencies.project import get_current_project, role_required, get_current_scan_id
from setezor.services import PortService
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/l4",
    tags=["Resource"],
)


@router.get("")
async def list_resources(
    port_service: Annotated[PortService, Depends(PortService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[dict]:
    return await port_service.get_resources(project_id=project_id)


@router.get("/{l4_id}/vulnerabilities")
async def list_resource_vulnerabilities(
    port_service: Annotated[PortService, Depends(PortService.new_instance)],
    l4_id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await port_service.list_vulnerabilities(l4_id=l4_id, project_id=project_id)

@router.post("/{l4_id}/vulnerabilities")
async def add_resource_vulnerability(
    port_service: Annotated[PortService, Depends(PortService.new_instance)],
    l4_id: str,
    data: dict,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    await port_service.add_vulnerability(project_id=project_id, id=l4_id, data=data)
    return Response(status_code=201)

@router.get("/get_resources_for_snmp")
async def get_resources_for_snmp(
    port_service: Annotated[PortService, Depends(PortService.new_instance)],
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project)
) -> list:
    return await port_service.get_resources_for_snmp(project_id=project_id, scan_id=scan_id)
