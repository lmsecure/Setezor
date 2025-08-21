

from sqlalchemy import text
from setezor.models import Object
from setezor.models.d_object_type import ObjectType
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, desc, or_, select, func
from sqlmodel.sql._expression_select_cls import Select

class ObjectRepository(SQLAlchemyRepository[Object]):
    model = Object


    async def exists(self, object_obj: Object):
        if object_obj.agent_id:
            stmt = select(Object).filter(Object.agent_id == object_obj.agent_id,
                                         Object.project_id == object_obj.project_id)
            result = await self._session.exec(stmt)
            return result.first()
        return False
    
    async def get_object_count(self, project_id: str, scans: list[str]):
        query = select(func.count(self.model.id).label('qty')).filter(self.model.project_id == project_id)

        addition = [self.model.scan_id == scan_id for scan_id in scans]
        query = query.filter(or_(*addition))
        result = await self._session.exec(query)
        return result.one()
    
    async def get_most_frequent_values_device_type(self, project_id: str, scans: list[str], limit: int | None = None):
        """Запрос на получение самых распространенных значений в колонке.
        
        Возвращает (значение, количество)
        """
        query = (
        select(
            ObjectType.name,
            func.count(ObjectType.name).label("count")
        ).join(Object, Object.object_type_id == ObjectType.id)\
        .filter(Object.project_id == project_id)\
        .group_by(ObjectType.name)\
        .order_by(desc("count"))\
        )
        
        addition = [Object.scan_id == scan_id for scan_id in scans]
        query = query.filter(or_(*addition))
        return await self._session.exec(query)