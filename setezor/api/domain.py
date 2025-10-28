from typing import Annotated
from fastapi import APIRouter, Depends, Response

from setezor.dependencies.project import get_current_project, role_required
from setezor.models.role import Role
from setezor.schemas.roles import Roles
from setezor.services.domain_service import DomainsService
from setezor.services.dns_service import DNS_Service
from setezor.services.role_service import RoleService



router = APIRouter(prefix="/domain", tags=["Domain"])

@router.post("/{id}/add_domain")
async def add_domain(
    domain_service: Annotated[DomainsService, Depends(DomainsService.new_instance)],
    dns_a_service: Annotated[DNS_Service, Depends(DNS_Service.new_instance)],
    id: str,
    data: dict,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    domain = data.get("domain")
    ip_id = id
    created_domain = await domain_service.add_domain(
        ip_id=ip_id,
        project_id=project_id,
        domain=domain,
    )
    created_dns_a = await dns_a_service.add_dns(
        ip_id=id,
        target_domain_id=created_domain.id,
        target_ip_id=ip_id
    )

    return Response(status_code=201)

@router.delete("/{id}/delete_domain")
async def delete_domain(
    domain_service: Annotated[DomainsService, Depends(DomainsService.new_instance)],
    dns_a_service: Annotated[DNS_Service, Depends(DNS_Service.new_instance)],
    id: str,
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    dns_a = await dns_a_service.get_by_domain_id(id)
    await dns_a_service.delete_by_dns_a_id(dns_a.id)
    await domain_service.delete_by_domain_id(id)

    return Response(status_code=201)

@router.patch("/{id}")
async def update_domain(
    domain_service: Annotated[DomainsService, Depends(DomainsService.new_instance)],
    id: str,
    domain: dict,
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    await domain_service.update_by_domain_id(id=id,
                                             domain=domain)

    return Response(status_code=200)