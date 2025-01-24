from pydantic import BaseModel


class ProjectPickForm(BaseModel):
    project_id: str


class ProjectCreateForm(BaseModel):
    name: str

class SearchVulnsSetTokenForm(BaseModel):
    token: str