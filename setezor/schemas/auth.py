from pydantic import BaseModel



class RegisterForm(BaseModel):
    login: str
    password: str
    password_confirmation: str
    invite_token: str