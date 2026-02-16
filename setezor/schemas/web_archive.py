from pydantic import BaseModel


class WebArchiveDomainResponse(BaseModel):
    archive_id: str
    domain: str