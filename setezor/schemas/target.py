from typing import Optional
from pydantic import BaseModel
from pydantic.networks import IPv4Network




class TargetCreateForm(BaseModel):
    ip: Optional[IPv4Network] = ""
    domain: Optional[str] = ""
    port: Optional[int] = None
    protocol: Optional[str] = ""
    
class TargetCreate(BaseModel):
    targets: list[TargetCreateForm]