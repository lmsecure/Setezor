from setezor.models import User
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class UserRepository(SQLAlchemyRepository[User]):
    model = User

    async def exists(self, route_obj: SQLModel):
        return False