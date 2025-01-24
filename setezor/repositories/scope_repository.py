from setezor.models import Scope
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class ScopeRepository(SQLAlchemyRepository[Scope]):
    model = Scope
