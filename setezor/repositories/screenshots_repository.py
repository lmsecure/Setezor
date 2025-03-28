from setezor.models import Screenshot, L7Software, L7SoftwareVulnerability, L7SoftwareVulnerabilityScreenshot, L4Software, L4SoftwareVulnerability, L4SoftwareVulnerabilityScreenshot
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select, func



class ScreenshotsRepository(SQLAlchemyRepository[Screenshot]):
    model = Screenshot


    async def count_on_l4(self, project_id: str, l4_id: str):
        stmt = select(L4SoftwareVulnerability.vulnerability_id, func.count(L4SoftwareVulnerabilityScreenshot.id)).select_from(L4Software)\
            .join(L4SoftwareVulnerability, L4SoftwareVulnerability.l4_software_id == L4Software.id)\
            .join(L4SoftwareVulnerabilityScreenshot, L4SoftwareVulnerabilityScreenshot.l4_software_vulnerability_id == L4SoftwareVulnerability.id, isouter=True)\
            .filter(L4Software.project_id == project_id, L4Software.l4_id == l4_id)\
            .group_by(L4SoftwareVulnerability.vulnerability_id)
        result = await self._session.exec(stmt)
        return result.all()


    async def count_on_l7(self, project_id: str, l7_id: str):
        stmt = select(L7SoftwareVulnerability.vulnerability_id, func.count(L7SoftwareVulnerabilityScreenshot.id)).select_from(L7Software)\
            .join(L7SoftwareVulnerability, L7SoftwareVulnerability.l7_software_id == L7Software.id)\
            .join(L7SoftwareVulnerabilityScreenshot, L7SoftwareVulnerabilityScreenshot.l7_software_vulnerability_id == L7SoftwareVulnerability.id, isouter=True)\
            .filter(L7Software.project_id == project_id, L7Software.l7_id == l7_id)\
            .group_by(L7SoftwareVulnerability.vulnerability_id)
        result = await self._session.exec(stmt)
        return result.all()