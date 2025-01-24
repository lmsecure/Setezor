from setezor.models import DNS_CNAME
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class DNS_CNAME_Repository(SQLAlchemyRepository[DNS_CNAME]):
    model = DNS_CNAME


    async def exists(self, dns_cname_obj: SQLModel):
        return False