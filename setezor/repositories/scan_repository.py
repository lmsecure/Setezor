from setezor.models import Scan
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class ScanRepository(SQLAlchemyRepository[Scan]):
    model = Scan
