from typing import Optional

from pydantic import BaseModel, Field


class AgentDisplay(BaseModel):
    name: str
    description: Optional[str]
    rest_url: str
    user_id: str | None = None
    flag: bool | None = False


class AgentAdd(AgentDisplay):
    secret_key: Optional[str] = ''


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(min_length=1, max_length=32)
    description: Optional[str]
    rest_url: Optional[str]


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


class AgentParents(BaseModel):
    parents: dict[str, bool]


class AgentAddToProject(BaseModel):
    agents: dict[str, bool]

