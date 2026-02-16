from setezor.models import Project
from setezor.repositories import SQLAlchemyRepository


class ProjectRepository(SQLAlchemyRepository[Project]):
    model = Project
