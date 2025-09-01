from typing import Annotated

from fastapi import APIRouter, Depends, Response

from setezor.dependencies.project import get_current_project, role_required
from setezor.schemas.roles import Roles
from setezor.services.dns_a_screenshot_service import DNSAScreenshotService

router = APIRouter(prefix="/dns_a_screenshot", tags=["DNS A Screenshot"])


@router.get("/list")
async def get_dns_a_screenshots(
    dns_a_screenshot_service: Annotated[
        DNSAScreenshotService, Depends(DNSAScreenshotService.new_instance)
    ],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer])),
) -> list:
    """Получить список всех DNS A Screenshot результатов для проекта"""
    return await dns_a_screenshot_service.get_screenshots_list(project_id=project_id)


@router.get("/screenshot/{screenshot_id}")
async def get_screenshot_file(
    screenshot_id: str,
    dns_a_screenshot_service: Annotated[
        DNSAScreenshotService, Depends(DNSAScreenshotService.new_instance)
    ],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer])),
) -> Response:
    """Получить файл скриншота по ID"""
    file_content = await dns_a_screenshot_service.get_screenshot_file(
        screenshot_id=screenshot_id, project_id=project_id
    )
    return Response(content=file_content, media_type="image/png")


@router.get("/by_domain/{domain}")
async def get_screenshots_by_domain(
    domain: str,
    dns_a_screenshot_service: Annotated[
        DNSAScreenshotService, Depends(DNSAScreenshotService.new_instance)
    ],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer])),
) -> list:
    """Получить скриншоты для конкретного домена"""
    return await dns_a_screenshot_service.get_screenshots_by_domain(
        domain=domain, project_id=project_id
    )


@router.get("/by_ip/{ip}")
async def get_screenshots_by_ip(
    ip: str,
    dns_a_screenshot_service: Annotated[
        DNSAScreenshotService, Depends(DNSAScreenshotService.new_instance)
    ],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer])),
) -> list:
    """Получить скриншоты для конкретного IP"""
    return await dns_a_screenshot_service.get_screenshots_by_ip(ip=ip, project_id=project_id)
