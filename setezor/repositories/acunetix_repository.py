from setezor.models import Acunetix
from setezor.repositories import SQLAlchemyRepository

class AcunetixRepository(SQLAlchemyRepository[Acunetix]):
    model = Acunetix
