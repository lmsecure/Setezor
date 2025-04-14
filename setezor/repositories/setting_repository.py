from setezor.models import Settings
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select

class SettingRepository(SQLAlchemyRepository[Settings]):
    model = Settings

    async def exists(self, settings_obj: SQLModel):
        stmt = select(Settings).filter(Settings.name == settings_obj.name)
        result = await self._session.exec(stmt)
        return result.first()