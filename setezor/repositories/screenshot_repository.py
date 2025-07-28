from sqlmodel import select

from setezor.models import Screenshot
from setezor.repositories import SQLAlchemyRepository


class ScreenshotRepository(SQLAlchemyRepository[Screenshot]):
    model = Screenshot

    async def exists(self, screenshot_obj: Screenshot):
        """
        Проверяет, существует ли уже скриншот с таким путем в проекте.

        Args:
            screenshot_obj: Объект Screenshot для проверки

        Returns:
            Screenshot или None, если скриншот не найден
        """
        if not screenshot_obj.path:
            return None

        stmt = select(Screenshot).where(
            Screenshot.path == screenshot_obj.path,
            Screenshot.project_id == screenshot_obj.project_id,
            Screenshot.scan_id == screenshot_obj.scan_id,
        )
        result = await self._session.exec(stmt)
        return result.first()
