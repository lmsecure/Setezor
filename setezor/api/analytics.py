import json
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from setezor.dependencies.project import get_current_project, role_required
from setezor.services import AnalyticsService
from setezor.schemas.roles import Roles

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

@router.get("/software")
async def analytics_l4_software(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    project_id: str = Depends(get_current_project),
    scans: list[str] = Query([]),
    page: int = Query(1, alias="page"),
    size: int = Query(10, alias="size"),
    sort: str = Query("[]", alias="sort"),
    filter: str = Query("[]", alias="filter"),

    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> JSONResponse:
    total, data = await analytics_service.get_l4_software_tabulator_data(
        project_id=project_id,
        scans = scans,
        page=page,
        size=size,
        sort=sort,
        filter=filter
    )
    
    last_page = (total + size - 1) // size
    return JSONResponse(content={"data": data, "last_page": last_page})

@router.get("/ip_mac_port")
async def analytics_ip_mac_port(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    project_id: str = Depends(get_current_project),
    scans: list[str] = Query([]),
    page: int = Query(1, alias="page"),
    size: int = Query(10, alias="size"),
    sort: str = Query("[]", alias="sort"),
    filter: str = Query("[]", alias="filter"),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> JSONResponse:
        total, data = await analytics_service.get_ip_mac_port_tabulator_data(
            project_id=project_id,
            scans=scans,
            page=page, 
            size=size,
            sort=sort,
            filter=filter)
        last_page = (total + size - 1) // size
        return JSONResponse(content={"data": data, "last_page": last_page})

@router.get("/domain_ip")
async def analytics_domain_ip(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    project_id: str = Depends(get_current_project),
    scans: list[str] = Query([]),
    page: int = Query(1, alias="page"),
    size: int = Query(10, alias="size"),
    sort: str = Query("[]", alias="sort"),
    filter: str = Query("[]", alias="filter"),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> JSONResponse:
        total, data = await analytics_service.get_domain_ip_tabulator_data(
            project_id=project_id,
            scans=scans,
            page=page, 
            size=size,
            sort=sort,
            filter=filter)
        last_page = (total + size - 1) // size
        return JSONResponse(content={"data": data, "last_page": last_page})

@router.get("/soft_vuln_link")
async def analytics_soft_vuln_link(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    project_id: str = Depends(get_current_project),
    scans: list[str] = Query([]),
    page: int = Query(1, alias="page"),
    size: int = Query(10, alias="size"),
    sort: str = Query("[]", alias="sort"),
    filter: str = Query("[]", alias="filter"),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> JSONResponse:
        total, data = await analytics_service.get_l4_soft_vuln_link_tabulator_data(
            project_id=project_id,
            scans=scans,
            page=page, 
            size=size,
            sort=sort,
            filter=filter)
        last_page = (total + size - 1) // size
        return JSONResponse(content={"data": data, "last_page": last_page})

@router.get("/auth_credentials")
async def get_auth_credentials(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    project_id: str = Depends(get_current_project),
    scans: list[str] = Query([]),
    page: int = Query(1, alias="page"),
    size: int = Query(10, alias="size"),
    sort: str = Query("[]", alias="sort"),
    filter: str = Query("[]", alias="filter"),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> JSONResponse:
        total, data = await analytics_service.get_auth_credentials(
            project_id=project_id,
            scans = scans,
            page=page, 
            size=size,
            sort=sort,
            filter=filter)
        last_page = (total + size - 1) // size
        return JSONResponse(content={"data": data, "last_page": last_page})


@router.get("/get_device_types")
async def get_device_types(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> dict:
    return await analytics_service.get_device_types(project_id=project_id, scans=scans)

@router.get("/get_object_count")
async def get_object_count(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> int:
    return await analytics_service.get_object_count(project_id=project_id, scans=scans)

@router.get("/get_ip_count")
async def get_ip_count(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> int:
    return await analytics_service.get_ip_count(project_id=project_id, scans=scans)

@router.get("/get_mac_count")
async def get_mac_count(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> int:
    return await analytics_service.get_mac_count(project_id=project_id, scans=scans)

@router.get("/get_port_count")
async def get_port_count(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> int:
    return await analytics_service.get_port_count(project_id=project_id, scans=scans)

@router.get("/get_software_version_cpe")
async def get_software_version_cpe(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> dict:
    return await analytics_service.get_software_version_cpe(project_id=project_id, scans=scans)

@router.get("/get_top_products")
async def get_top_products(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[tuple]:
    return await analytics_service.get_top_products(project_id=project_id)

@router.get("/get_top_ports")
async def get_top_ports(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[tuple]:
    return await analytics_service.get_top_ports(project_id=project_id)

@router.get("/get_top_protocols")
async def get_top_protocols(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[tuple]:
    return await analytics_service.get_top_protocols(project_id=project_id)

@router.get("/get_vulnerabilities")
async def get_vulnerabilities(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> dict:
    return await analytics_service.get_vulnerabilities(project_id=project_id, scans=scans)

@router.get("/get_ports_and_protocols")
async def get_ports_and_protocols(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> dict:
    return await analytics_service.get_ports_and_protocols(project_id=project_id, scans=scans)

@router.get("/get_products_and_service_name")
async def get_products_and_service_name(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> dict:
    return await analytics_service.get_products_and_service_name(project_id=project_id, scans=scans)


@router.get("/dns_a_screenshot")
async def analytics_dns_a_screenshot(
    analytics_service: Annotated[AnalyticsService, Depends(AnalyticsService.new_instance)],
    project_id: str = Depends(get_current_project),
    scans: list[str] = Query([]),
    page: int = Query(1, alias="page"),
    size: int = Query(10, alias="size"),
    sort: str = Query("[]", alias="sort"),
    filter: str = Query("[]", alias="filter"),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> JSONResponse:
        total, data = await analytics_service.get_dns_a_screenshot_tabulator_data_optimized(
            project_id=project_id,
            scans=scans, 
            page=page, 
            size=size,
            sort=sort,
            filter=filter)
        last_page = (total + size - 1) // size
        return JSONResponse(content={"data": data, "last_page": last_page})
