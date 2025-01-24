from setezor.models import Cert
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class CertRepository(SQLAlchemyRepository[Cert]):
    model = Cert


    async def exists(self, cert_obj: SQLModel):
        return False