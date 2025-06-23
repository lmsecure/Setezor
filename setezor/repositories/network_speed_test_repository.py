
from sqlmodel import select, or_
from setezor.models import NetworkSpeedTest
from setezor.repositories import SQLAlchemyRepository


class NetworkSpeedTestRepository(SQLAlchemyRepository[NetworkSpeedTest]):
    model = NetworkSpeedTest

    async def exists(self, new_obj):
        stmt = select(self.model).filter(
            self.model.project_id == new_obj.project_id,
            self.model.scan_id == new_obj.scan_id,
            self.model.ip_id_from == new_obj.ip_id_from,
            self.model.ip_id_to == new_obj.ip_id_to,
            self.model.port == new_obj.port,
            self.model.protocol == new_obj.protocol
        )
        result = await self._session.exec(stmt)
        obj = result.first()
        if not obj:
            return
        obj.speed = new_obj.speed
        return obj


    async def get_edges(self, project_id: str, scans: list[str]):
        stmt = select(self.model.ip_id_from, self.model.ip_id_to).filter(self.model.project_id == project_id)
        addition = [self.model.scan_id == scan_id for scan_id in scans]
        addition.append(self.model.scan_id == None)
        stmt = stmt.filter(or_(*addition)).group_by(self.model.ip_id_from, self.model.ip_id_to)
        return await self._session.exec(stmt)