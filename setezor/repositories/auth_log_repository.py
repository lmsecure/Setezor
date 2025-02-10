from setezor.models import AuthLog
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class AuthLog_Repository(SQLAlchemyRepository[AuthLog]):
    model = AuthLog
