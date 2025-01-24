from pydantic import BaseModel

class UserAuth(BaseModel):
    login: str
    password: str