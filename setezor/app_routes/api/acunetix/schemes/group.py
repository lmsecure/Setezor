from pydantic import BaseModel


class Vuln(BaseModel):
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class GroupForm(BaseModel):
    name: str
    description: str


class Group(GroupForm):
    group_id: str
    target_count: int | None = 0
    description: str | None = None
    vuln_count: Vuln | None = None

class GroupTargets(BaseModel):
    target_id_list : list[str]