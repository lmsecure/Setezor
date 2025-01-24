from pydantic import BaseModel


class ObjectSchema(BaseModel):
    id: int
    object_type: str | None

    class Config:
        from_attributes = True


class ObjectSchemaAdd(BaseModel):
    object_type: str | None
