from setezor.models import DNS_A
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class DNS_A_Repository(SQLAlchemyRepository[DNS_A]):
    model = DNS_A


    async def exists(self, dns_obj: SQLModel):
        return False