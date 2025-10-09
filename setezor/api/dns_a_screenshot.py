from typing import Annotated

from fastapi import APIRouter, Depends, Response

from setezor.dependencies.project import get_current_project, get_current_scan_id, role_required
from setezor.schemas.roles import Roles
from setezor.services.dns_a_screenshot_service import DNSAScreenshotService

router = APIRouter(prefix="/dns_a_screenshot", tags=["DNS A Screenshot"])


@router.get("/screenshot/{screenshot_id}")
async def get_screenshot_file(
    screenshot_id: str,
    dns_a_screenshot_service: Annotated[
        DNSAScreenshotService, Depends(DNSAScreenshotService.new_instance)
    ],
    project_id: str = Depends(get_current_project),
    scan_id: str = Depends(get_current_scan_id),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer])),
) -> Response:
    """Получить файл скриншота по ID"""
    file_content = await dns_a_screenshot_service.get_screenshot_file(
        project_id=project_id, scan_id=scan_id,
        screenshot_id=screenshot_id
    )
    return Response(content=file_content, media_type="image/png")
