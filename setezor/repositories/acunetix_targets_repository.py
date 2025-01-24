from setezor.models import AcunetixTargets
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class AcunetixTargetsRepository(SQLAlchemyRepository[AcunetixTargets]):
    model = AcunetixTargets


    async def exists(self, acunetix_targets_obj: SQLModel):
        return False