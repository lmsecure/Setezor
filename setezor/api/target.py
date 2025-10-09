from typing import Annotated
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from setezor.schemas.roles import Roles
from setezor.dependencies.project import get_current_project, role_required
from setezor.services.target_service import TargetService
from setezor.services.ip_service import IPService
from setezor.services.domain_service import DomainsService
from setezor.schemas.target import TargetCreateForm

router = APIRouter(prefix="/target")


@router.delete("/{target_id}", status_code=204)
async def delete_target(
    target_id: str,
    target_service: Annotated[TargetService, Depends(TargetService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))          
):
    await target_service.delete_target_by_id(target_id=target_id)

@router.put("/{target_id}", status_code=200)
async def update_target(
    target_id: str,
    target_service: Annotated[TargetService, Depends(TargetService.new_instance)],
    updated_data: TargetCreateForm,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))          
) -> None:
    await target_service.update_target_by_id(target_id=target_id,
                                             updated_data=updated_data)

@router.get("/get_ips")
async def get_ips_for_target(
    ip_service: Annotated[IPService, Depends(IPService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await ip_service.list_ips(project_id=project_id)


@router.get("/get_domains")
async def get_domains_for_target(
    domain_service: Annotated[DomainsService, Depends(DomainsService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await domain_service.list_domains(project_id=project_id)


@router.get("/get_ips_ports")
async def get_ips_and_port_for_target(
    ip_service: Annotated[IPService, Depends(IPService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await ip_service.get_ips_and_ports(project_id=project_id)


@router.get("/get_all_data")
async def get_all_data_for_target(
    target_service: Annotated[TargetService, Depends(TargetService.new_instance)],
    project_id: str = Depends(get_current_project),
    scans: list[str] = Query([]),
    page: int = Query(1, alias="page"),
    size: int = Query(10, alias="size"),
    sort: str = Query("[]", alias="sort"),
    filter: str = Query("[]", alias="filter"),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> JSONResponse:
    total, data = await target_service.get_l4_data_for_target_wrapper(
        project_id=project_id,
        scans=scans,
        page=page,
        size=size,
        sort=sort,
        filter=filter
    )

    if isinstance(data, dict) and data.get("error"):
        return JSONResponse(content={"error": data["error"]}, status_code=500)

    last_page = (total + size - 1) // size

    return JSONResponse(content={"data": data, "last_page": last_page})

