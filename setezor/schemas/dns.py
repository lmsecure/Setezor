from pydantic import BaseModel


class DNSSchema(BaseModel):
    id: int
    record_type: str
    record_value: str
    domain_id: int

    class Config:
        from_attributes = True


class DNSSchemaAdd(BaseModel):
    record_type: str
    record_value: str
    domain_id: int
