

from sqlalchemy import text
from setezor.models import Object
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select, func
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
    
    async def get_object_count(self, project_id: str, last_scan_id: str):
        object_count: Select = select(func.count(self.model.id).label('qty')).filter(self.model.project_id == project_id, self.model.scan_id == last_scan_id)

        result = await self._session.exec(object_count)
        object_count_result = result.one()

        return object_count_result
    
    async def get_most_frequent_values_device_type(self, project_id: str, last_scan_id: str, limit: int | None = None):
        """Запрос на получение самых распространенных значений в колонке.
        
        Возвращает (значение, количество)
        """
        device_types_query = text("""
            SELECT setezor_d_object_type.name, COUNT(setezor_d_object_type.name) AS count
            FROM object
            JOIN setezor_d_object_type ON object.object_type_id = setezor_d_object_type.id
            WHERE object.project_id = :project_id
            AND object.scan_id = :last_scan_id
            GROUP BY setezor_d_object_type.name
            ORDER BY count DESC
        """)

        result = await self._session.exec(device_types_query, params={'project_id': project_id, 'last_scan_id': last_scan_id})
        return result.fetchall()