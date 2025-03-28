from typing import Optional
from pydantic import BaseModel
from pydantic.networks import IPv4Address




class TargetCreateForm(BaseModel):
    ip: Optional[IPv4Address] = ""
    domain: Optional[str] = ""
    port: Optional[int] = None
    protocol: Optional[str] = ""
    
class TargetCreate(BaseModel):
    targets: str | list[TargetCreateForm]