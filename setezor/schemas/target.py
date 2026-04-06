from typing import Optional
from pydantic import BaseModel
from pydantic.networks import IPv4Network
from setezor.schemas.domain import DomainStr



class TargetCreateForm(BaseModel):
    ip: Optional[IPv4Network] = ""
    domain: Optional[DomainStr] = ""
    port: Optional[int] = None
    protocol: Optional[str] = ""
    
class TargetCreate(BaseModel):
    targets: list[TargetCreateForm]