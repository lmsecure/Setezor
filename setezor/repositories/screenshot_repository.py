from setezor.models import Screenshot
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select

class ScreenshotRepository(SQLAlchemyRepository[Screenshot]):
    model = Screenshot
