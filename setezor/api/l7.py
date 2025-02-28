
from fastapi import APIRouter, Depends, Response
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, role_required, get_current_scan_id
from setezor.services import L7Service

router = APIRouter(
    prefix="/resource",
    tags=["Resource"],
)

@router.get("")
async def list_resources(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner", "viewer"]))
) -> list[dict]:
    return await L7Service.list(uow=uow, project_id=project_id)


@router.get("/{l7_id}/vulnerabilities")
async def list_resource_vulnerabilities(
    uow: UOWDep,
    l7_id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner", "viewer"]))
):
    return await L7Service.list_vulnerabilities(uow=uow, l7_id=l7_id, project_id=project_id)

@router.post("/{l7_id}/vulnerabilities")
async def add_resource_vulnerability(
    uow: UOWDep,
    l7_id: str,
    data: dict,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
):
    await L7Service.add_vulnerability(uow=uow, project_id=project_id, id=l7_id, data=data)
    return Response(status_code=201)

@router.get("/get_resources_for_snmp")
async def get_resources_for_snmp(
    uow: UOWDep,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project)
) -> list:
    return await L7Service.get_resources_for_snmp(uow=uow, project_id=project_id, scan_id=scan_id)
