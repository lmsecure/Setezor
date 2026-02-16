from typing import Annotated
from fastapi import APIRouter, Depends
from starlette.responses import FileResponse

from setezor.dependencies.project import get_current_project, get_scan_id, role_required
from setezor.schemas.roles import Roles
from setezor.services.web_archive_service import WebArchiveService

router = APIRouter(
    prefix="/web_archives",
    tags=["WebArchive"],
)


@router.get("/{task_id}")
async def get_web_archive(
    task_id: str,
    web_archive_service: Annotated[WebArchiveService, Depends(WebArchiveService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> FileResponse:
    return await web_archive_service.get_web_archive(task_id, user_id, project_id)
