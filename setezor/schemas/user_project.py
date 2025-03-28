from pydantic import BaseModel


class UserChangeRoleInProjectForm(BaseModel):
    user_id: str
    role_id: str