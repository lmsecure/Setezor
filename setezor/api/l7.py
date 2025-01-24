
from fastapi import APIRouter, Depends, Response
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project
from setezor.services import L7Service

router = APIRouter(
    prefix="/resource",
    tags=["Resource"],
)

@router.get("")
async def list_resources(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list[dict]:
    return await L7Service.list(uow=uow, project_id=project_id)


@router.get("/{l7_id}/vulnerabilities")
async def list_resource_vulnerabilities(
    uow: UOWDep,
    l7_id: str,
    project_id: str = Depends(get_current_project)
):
    return await L7Service.list_vulnerabilities(uow=uow, l7_id=l7_id, project_id=project_id)

@router.post("/{l7_id}/vulnerabilities")
async def add_resource_vulnerability(
    uow: UOWDep,
    l7_id: str,
    data: dict,
    project_id: str = Depends(get_current_project)
):
    await L7Service.add_vulnerability(uow=uow, project_id=project_id, id=l7_id, data=data)
    return Response(status_code=201)