from pydantic import BaseModel, BeforeValidator
from pydantic_core import PydanticCustomError
from typing import Annotated, Any

def validate_domain(v: Any) -> str:
    if not isinstance(v, str):
        raise PydanticCustomError('domain_type', 'Value must be a string')
    
    v = v.strip().lower()
    
    if len(v) < 1 or len(v) > 500:
        raise PydanticCustomError('domain_length', 'Domain must be between 1 and 500 characters')

    return v

DomainStr = Annotated[str, BeforeValidator(validate_domain)]

class DomainSchema(BaseModel):
    id: int
    domain: DomainStr
    ip_id: int

    class Config:
        from_attributes = True


class DomainSchemaAdd(BaseModel):
    domain: DomainStr
    ip_id: int
