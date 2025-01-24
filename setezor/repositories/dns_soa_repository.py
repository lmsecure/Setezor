from setezor.models import DNS_SOA
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class DNS_SOA_Repository(SQLAlchemyRepository[DNS_SOA]):
    model = DNS_SOA


    async def exists(self, dns_a_obj: SQLModel):
        return False