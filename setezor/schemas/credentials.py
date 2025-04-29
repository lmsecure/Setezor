from typing import Optional
from pydantic import BaseModel



class CredentialsForm(BaseModel):
    port_id: str
    login: str
    password: Optional[str] = None
    need_auth: bool
    permissions: int
    parameters: Optional[str] = None