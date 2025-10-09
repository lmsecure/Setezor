import os

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

    async def get_screenshot_file(self, project_id: str, scan_id: str, screenshot_id: str) -> bytes:
        """Получить файл скриншота по ID"""
        async with self._uow:
            screenshot = await self._uow.screenshot.find_one(project_id=project_id, scan_id=scan_id, id=screenshot_id)
        file_path = os.path.join(PROJECTS_DIR_PATH, project_id, scan_id, "screenshots", f"{screenshot_id}.png")
        if not screenshot:
            raise FileNotFoundError(f"Screenshot file not found for ID: {screenshot_id}")
        if not screenshot.path or not os.path.exists(file_path):
            file_path = os.path.join(PROJECTS_DIR_PATH, project_id, scan_id, "screenshots", screenshot.path.split('/')[-1])
        if not screenshot.path or not os.path.exists(file_path):
            raise FileNotFoundError(f"Screenshot file not found for ID: {screenshot_id}")
        with open(file_path, "rb") as f:
            return f.read()
