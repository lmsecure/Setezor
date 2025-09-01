import os

from setezor.services.base_service import BaseService



class DNSAScreenshotService(BaseService):

    @classmethod
    def from_db_row(cls, screenshots_data) -> dict:
        return {
            "id": screenshots_data.id,
            "screenshot_id": screenshots_data.screenshot_id,
            "domain": screenshots_data.domain,
            "ip": screenshots_data.ip,
            "screenshot_path": screenshots_data.screenshot_path,
            "created_at": screenshots_data.created_at,
        }

    async def get_screenshots_list(self, project_id: str) -> list:
        """Получить список всех скриншотов для проекта"""
        async with self._uow:
            screenshots_data = await self._uow.dns_a_screenshot.get_screenshots_with_info(
                project_id=project_id
            )
        return DNSAScreenshotService.from_db_data(screenshots_data)

    async def get_screenshots_by_domain(
        self, domain: str, project_id: str
    ) -> list:
        """Получить скриншоты для конкретного домена"""
        async with self._uow:
            screenshots_data = await self._uow.dns_a_screenshot.get_screenshots_by_domain(
                domain=domain, project_id=project_id
            )
        return DNSAScreenshotService.from_db_data(screenshots_data)

    async def get_screenshots_by_ip(self, ip: str, project_id: str) -> list:
        """Получить скриншоты для конкретного IP"""
        async with self._uow:
            screenshots_data = await self._uow.dns_a_screenshot.get_screenshots_by_ip(
                ip=ip, project_id=project_id
            )
        return DNSAScreenshotService.from_db_data(screenshots_data)

    async def get_screenshot_file(self, screenshot_id: str, project_id: str) -> bytes:
        """Получить файл скриншота по ID"""
        async with self._uow:
            screenshot = await self._uow.screenshot.find_one(
                id=screenshot_id, project_id=project_id
            )

        if not screenshot or not screenshot.path or not os.path.exists(screenshot.path):
            raise FileNotFoundError(f"Screenshot file not found for ID: {screenshot_id}")

        with open(screenshot.path, "rb") as f:
            return f.read()
