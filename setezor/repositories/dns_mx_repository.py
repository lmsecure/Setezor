from setezor.models import DNS_MX
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class DNS_MX_Repository(SQLAlchemyRepository[DNS_MX]):
    model = DNS_MX


    async def exists(self, dns_a_obj: SQLModel):
        return False