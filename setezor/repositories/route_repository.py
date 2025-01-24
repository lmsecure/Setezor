from setezor.models import Route
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class RouteRepository(SQLAlchemyRepository[Route]):
    model = Route

    async def exists(self, route_obj: SQLModel):
        return False