from fastapi import APIRouter, Depends
from setezor.schemas.roles import Roles
from setezor.dependencies.project import get_current_project, role_required
from setezor.dependencies.uow_dependency import UOWDep
from setezor.services.target_service import TargetService
from setezor.services.ip_service import IPService
from setezor.services.domain_service import DomainsService
from setezor.schemas.target import TargetCreateForm

router = APIRouter(prefix="/target")


@router.delete("/{target_id}", status_code=204)
async def delete_target(
    target_id: str,
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))          
) -> None:
    await TargetService.delete_target_by_id(uow=uow, target_id=target_id)

@router.put("/{target_id}", status_code=200)
async def update_target(
    target_id: str,
    uow: UOWDep,
    updated_data: TargetCreateForm,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))          
) -> None:
    await TargetService.update_target_by_id(uow=uow,
                                            target_id=target_id, 
                                            updated_data=updated_data)

@router.get("/get_ips")
async def get_ips_for_target(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await IPService.list_ips(uow=uow, project_id=project_id)


@router.get("/get_domains")
async def get_domains_for_target(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await DomainsService.list_domains(uow=uow, project_id=project_id)


@router.get("/get_ips_ports")
async def get_ips_and_port_for_target(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await IPService.get_ips_and_ports(uow=uow, project_id=project_id)