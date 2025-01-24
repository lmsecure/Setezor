from setezor.models import DNS_NS
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class DNS_NS_Repository(SQLAlchemyRepository[DNS_NS]):
    model = DNS_NS


    async def exists(self, dns_a_obj: SQLModel):
        return False