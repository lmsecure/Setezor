from setezor.models import Scan
from setezor.repositories import SQLAlchemyRepository


class ScanRepository(SQLAlchemyRepository[Scan]):
    model = Scan


