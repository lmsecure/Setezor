from pydantic import BaseModel
from setezor.schemas.domain import DomainStr

class WebArchiveDomainResponse(BaseModel):
    archive_id: str
    domain: DomainStr