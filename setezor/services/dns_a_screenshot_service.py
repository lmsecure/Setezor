import os

from fastapi import HTTPException
from fastapi.responses import FileResponse

from setezor.modules.site_parser.screenshoter import ScreenshotModule
from setezor.services.base_service import BaseService
from setezor.settings import PROJECTS_DIR_PATH


class DNSAScreenshotService(BaseService):

    @classmethod
    def from_db_row(cls, screenshots_data) -> dict:
        return {
            "id": screenshots_data.id,
            "screenshot_id": screenshots_data.screenshot_id,
            "domain": screenshots_data.domain,
            "ip": screenshots_data.ip,
            "screenshot_path": screenshots_data.id,
            "created_at": screenshots_data.created_at,
        }

    async def get_screenshot_file(self, project_id: str, user_id: str, task_id: str) -> FileResponse:
        """Получить файл скриншота по ID"""
        async with self._uow:
            task = await self._uow.task.find_one(id=task_id, user_id=user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        screenshot_name = ScreenshotModule.get_file_name_by_task_id(
            project_id=project_id, scan_id=task.scan_id, task_id=task_id
        )
        screenshot_path = os.path.join(PROJECTS_DIR_PATH, project_id, task.scan_id, 'screenshots', screenshot_name)
        return FileResponse(path=screenshot_path, media_type='image/png', filename=screenshot_name)
