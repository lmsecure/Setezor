from typing import Dict
from fastapi import APIRouter, Depends
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, role_required
from setezor.services import AnalyticsService
from setezor.schemas.roles import Roles

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

@router.get("/software")
async def analytics_l4_software(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await AnalyticsService.get_l4_software_tabulator_data(uow=uow, project_id=project_id)

@router.get("/ip_mac_port")
async def analytics_ip_mac_port(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await AnalyticsService.get_ip_mac_port_tabulator_data(uow=uow, project_id=project_id)

@router.get("/domain_ip")
async def analytics_domain_ip(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await AnalyticsService.get_domain_ip_tabulator_data(uow=uow, project_id=project_id)

@router.get("/soft_vuln_link")
async def analytics_soft_vuln_link(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await AnalyticsService.get_l4_soft_vuln_link_tabulator_data(uow=uow, project_id=project_id)

@router.get("/ip")
async def analytics_ip(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await AnalyticsService.get_ip_tabulator_data(uow=uow, project_id=project_id)

@router.get("/mac")
async def analytics_mac(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await AnalyticsService.get_mac_tabulator_data(uow=uow, project_id=project_id)

@router.get("/port")
async def analytics_port(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await AnalyticsService.get_port_tabulator_data(uow=uow, project_id=project_id)


@router.get("/auth_credentials")
async def get_auth_credentials(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list:
    return await AnalyticsService.get_auth_credentials(uow=uow, project_id=project_id)

@router.get("/get_device_types")
async def get_device_types(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> dict:
    return await AnalyticsService.get_device_types(uow=uow, project_id=project_id)

@router.get("/get_object_count")
async def get_object_count(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> int:
    return await AnalyticsService.get_object_count(uow=uow, project_id=project_id)

@router.get("/get_ip_count")
async def get_ip_count(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> int:
    return await AnalyticsService.get_ip_count(uow=uow, project_id=project_id)

@router.get("/get_mac_count")
async def get_mac_count(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> int:
    return await AnalyticsService.get_mac_count(uow=uow, project_id=project_id)

@router.get("/get_port_count")
async def get_port_count(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> int:
    return await AnalyticsService.get_port_count(uow=uow, project_id=project_id)

@router.get("/get_software_version_cpe")
async def get_software_version_cpe(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> dict:
    return await AnalyticsService.get_software_version_cpe(uow=uow, project_id=project_id)

@router.get("/get_top_products")
async def get_top_products(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[tuple]:
    return await AnalyticsService.get_top_products(uow=uow, project_id=project_id)

@router.get("/get_top_ports")
async def get_top_ports(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[tuple]:
    return await AnalyticsService.get_top_ports(uow=uow, project_id=project_id)

@router.get("/get_top_protocols")
async def get_top_protocols(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[tuple]:
    return await AnalyticsService.get_top_protocols(uow=uow, project_id=project_id)

@router.get("/get_vulnerabilities")
async def get_vulnerabilities(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> dict:
    return await AnalyticsService.get_vulnerabilities(uow=uow, project_id=project_id)

@router.get("/get_ports_and_protocols")
async def get_ports_and_protocols(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> dict:
    return await AnalyticsService.get_ports_and_protocols(uow=uow, project_id=project_id)

@router.get("/get_products_and_service_name")
async def get_products_and_service_name(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> dict:
    return await AnalyticsService.get_products_and_service_name(uow=uow, project_id=project_id)