from typing import Dict
from fastapi import APIRouter, Depends
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project
from setezor.services import AnalyticsService


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

@router.get("")
async def analytics(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> Dict:
    return await AnalyticsService.get_all_analytics(uow=uow, project_id=project_id)
    
@router.get("/l7_software")
async def analytics_l7_software(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list:
    return await AnalyticsService.get_l7_software_tabulator_data(uow=uow, project_id=project_id)

@router.get("/l4_software")
async def analytics_l4_software(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list:
    return await AnalyticsService.get_l4_software_tabulator_data(uow=uow, project_id=project_id)

@router.get("/ip_mac_port")
async def analytics_ip_mac_port(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list:
    return await AnalyticsService.get_ip_mac_port_tabulator_data(uow=uow, project_id=project_id)

@router.get("/domain_ip")
async def analytics_domain_ip(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list:
    return await AnalyticsService.get_domain_ip_tabulator_data(uow=uow, project_id=project_id)

@router.get("/l7_soft_vuln_link")
async def analytics_soft_vuln_link(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list:
    return await AnalyticsService.get_l7_soft_vuln_link_tabulator_data(uow=uow, project_id=project_id)

@router.get("/l4_soft_vuln_link")
async def analytics_soft_vuln_link(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list:
    return await AnalyticsService.get_l4_soft_vuln_link_tabulator_data(uow=uow, project_id=project_id)

@router.get("/ip")
async def analytics_ip(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list:
    return await AnalyticsService.get_ip_tabulator_data(uow=uow, project_id=project_id)

@router.get("/mac")
async def analytics_mac(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list:
    return await AnalyticsService.get_mac_tabulator_data(uow=uow, project_id=project_id)

@router.get("/port")
async def analytics_port(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list:
    return await AnalyticsService.get_port_tabulator_data(uow=uow, project_id=project_id)
