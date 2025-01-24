from typing import Optional
from pydantic import BaseModel




class TargetCreateForm(BaseModel):
    ip: Optional[str]
    domain: Optional[str]
    port: Optional[int]
    protocol: Optional[str]
    
class TargetCreate(BaseModel):
    targets: str | list[TargetCreateForm]