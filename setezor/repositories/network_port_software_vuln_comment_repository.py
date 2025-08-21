from sqlmodel import SQLModel

from setezor.models import L4SoftwareVulnerabilityComment
from setezor.repositories import SQLAlchemyRepository


class NetworkPortSoftwareVulnCommentRepository(SQLAlchemyRepository[L4SoftwareVulnerabilityComment]):
    model = L4SoftwareVulnerabilityComment

    async def exists(self, emp_obj: SQLModel):
        return False