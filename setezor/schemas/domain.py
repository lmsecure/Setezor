from pydantic import BaseModel


class DomainSchema(BaseModel):
    id: int
    domain: str
    ip_id: int

    class Config:
        from_attributes = True


class DomainSchemaAdd(BaseModel):
    domain: str
    ip_id: int
