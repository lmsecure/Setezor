from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import FileResponse

from setezor.dependencies.project import get_current_project, get_current_scan_id, role_required
from setezor.schemas.roles import Roles
from setezor.services.dns_a_screenshot_service import DNSAScreenshotService

router = APIRouter(prefix="/dns_a_screenshot", tags=["DNS A Screenshot"])


@router.get("/screenshot/{task_id}")
async def get_screenshot_file(
    task_id: str,
    dns_a_screenshot_service: Annotated[
        DNSAScreenshotService, Depends(DNSAScreenshotService.new_instance)
    ],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer])),
) -> FileResponse:
    """Получить файл скриншота по ID"""
    return await dns_a_screenshot_service.get_screenshot_file(
        project_id=project_id, user_id=user_id, task_id=task_id
    )
