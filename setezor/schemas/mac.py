from pydantic import BaseModel


class MACSchema(BaseModel):
    id: int
    mac: str
    object_id: int

    class Config:
        from_attributes = True


class MACSchemaAdd(BaseModel):
    mac: str | None
    object_id: int
