from setezor.models import ASN
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class ASN_Repository(SQLAlchemyRepository[ASN]):
    model = ASN


    async def exists(self, asn_obj: SQLModel):
        return False