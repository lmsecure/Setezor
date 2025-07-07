from typing import Optional
from pydantic import BaseModel



class AssignNodeAsInterfacePayload(BaseModel):
    agent_id: Optional[str] = ""
    agent_name: Optional[str] = ""
    agent_description: Optional[str] = ""
    ip_id: str
    interface_name: str