from typing import Optional
from pydantic import BaseModel

class ScopeCreateForm(BaseModel):
    name: str
    description: Optional[str]