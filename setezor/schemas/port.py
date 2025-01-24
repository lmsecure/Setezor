from pydantic import BaseModel


class PortSchema(BaseModel):
    id: int
    port: int
    ip_id: int

    class Config:
        from_attributes = True


class PortSchemaAdd(BaseModel):
    port: int
    ip_id: int
