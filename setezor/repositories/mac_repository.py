

from sqlalchemy import Select
from setezor.models import MAC, IP, ObjectType, Object, Vendor 
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select, func


class MACRepository(SQLAlchemyRepository[MAC]):
    model = MAC


    async def exists(self, mac_obj: MAC):
        if not mac_obj.mac:
            return None
        obj_id = mac_obj.object_id
        if obj_id:
            stmt = select(MAC).filter(MAC.mac == mac_obj.mac,
                                      MAC.object_id == obj_id, 
                                      MAC.project_id == mac_obj.project_id,
                                      MAC.scan_id==mac_obj.scan_id
                                      )
        else:
            stmt = select(MAC).filter(MAC.mac == mac_obj.mac, 
                                      MAC.project_id == mac_obj.project_id,
                                      MAC.scan_id==mac_obj.scan_id
                                      )
        result = await self._session.exec(stmt)
        return result.first()
    
    async def get_mac_count(self, project_id: str):
        
        """Считает количество сток"""
        
        mac_count: Select = select(func.count()).select_from(self.model).filter(self.model.project_id == project_id)

        result = await self._session.exec(mac_count)
        mac_count_result = result.one()
        return mac_count_result
    
    async def get_interfaces(self, object_id: int):
        stmt = select(MAC.id, MAC.name, MAC.mac, IP.id.label("ip_id"), IP.ip).join(IP, MAC.id == IP.mac_id).filter(MAC.object_id == object_id)
        result = await self._session.exec(stmt)
        return result.all()
    
    async def get_mac_tabulator_data(self, project_id: str):
        row_number_column = func.row_number().over(
        order_by=func.count(MAC.mac).desc()
        ).label("id")

        tabulator_dashboard_data = (
            select(
                row_number_column,
                MAC.mac,
                ObjectType.name,
                Vendor.name
            )
            .outerjoin(Vendor, MAC.vendor_id == Vendor.id)
            .outerjoin(Object, MAC.object_id  == Object.id)
            .outerjoin(ObjectType, Object.object_type_id  == ObjectType.id)
            .filter(MAC.project_id == project_id)
            .group_by(
                MAC.mac,
                ObjectType.name,
                Vendor.name
            )
            .order_by(func.count(MAC.mac).desc())
        )

        result = await self._session.exec(tabulator_dashboard_data)
        return result.all()