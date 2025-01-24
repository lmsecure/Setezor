from setezor.models import DNS_TXT
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class DNS_TXT_Repository(SQLAlchemyRepository[DNS_TXT]):
    model = DNS_TXT


    async def exists(self, dns_a_obj: SQLModel):
        return False