from typing import Optional

from pydantic import BaseModel


class AgentAdd(BaseModel):
    parent_agent_id: str
    name: str
    description: Optional[str]
    rest_url: str
    color: str
    secret_key: Optional[str] = ''


class AgentInterfacesChain(BaseModel):
    agents_chain: list[str]


class AgentColorChange(BaseModel):
    color: str


class InterfaceOfAgent(BaseModel):
    name: str
    ip: str
    mac: str


class BackWardData(BaseModel):
    sender: str
    data: str