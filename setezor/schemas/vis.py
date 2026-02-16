from typing import Literal

from pydantic import BaseModel


class Node(BaseModel):
    id: str
    address: str
    agents: list[str]
    agent: str | None
    parent_agent_id: bool | None = None
    object_type: str
    group: str
    value: int
    shape: Literal['triangle', 'square', 'rectangle', 'dot']
    is_server: bool
    label: str
