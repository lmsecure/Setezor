

from sqlalchemy import Select, case, desc
from setezor.models import Port, IP
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select, func

class PortRepository(SQLAlchemyRepository[Port]):
    model = Port

    async def exists(self, port_obj: Port):
        port = port_obj.port
        ip = port_obj.ip
        ip_id = port_obj.ip_id
        if ip_id:
            stmt = select(Port).join(IP, Port.ip_id == IP.id).filter(Port.port == port,
                                                                     IP.id == ip_id,
                                                                     Port.project_id == port_obj.project_id,
                                                                     Port.scan_id == port_obj.scan_id
                                                                     )
        else:
            stmt = select(Port).join(IP, Port.ip_id == IP.id).filter(Port.port == port, 
                                                                     IP.ip == ip.ip, 
                                                                     Port.project_id == port_obj.project_id,
                                                                     Port.scan_id == port_obj.scan_id
                                                                     )
        result = await self._session.exec(stmt)
        return result.first()
    
    async def get_port_count(self, project_id: str):
        
        """Считает количество сток"""
        
        port_count: Select = select(func.count()).select_from(self.model).filter(self.model.project_id == project_id)

        result = await self._session.exec(port_count)
        port_count_result = result.one()
        return port_count_result
    
    async def get_top_ports(self, project_id: str):
        
        top_ports: Select = select(self.model.port, func.count(self.model.port).label("count")).group_by(self.model.port).order_by(desc("count")).filter(self.model.project_id == project_id)

        result = await self._session.exec(top_ports)
        top_ports_result = result.all()
        return top_ports_result
    
    async def get_top_protocols(self, project_id: str):
                
        stmt_protocols = select(
                case(
                    (Port.protocol.is_(None), "unknown"),
                    (Port.protocol == "", "unknown"),
                    else_=Port.protocol
                ).label("labels"),
                func.count(Port.protocol).label("values")
            ).filter(Port.project_id == project_id)\
            .group_by(Port.protocol)\
            .order_by(func.count(Port.protocol).desc()) 

        result = await self._session.exec(stmt_protocols)
        top_protocols_result = result.all()
        return top_protocols_result
    
    async def get_port_tabulator_data(self, project_id: str):
        row_number_column = func.row_number().over(
        order_by=func.count(Port.port).desc()
        ).label("id")

        tabulator_dashboard_data = (
            select(
                row_number_column,
                IP.ip,
                Port.port,
                Port.protocol,
                Port.service_name,
            )
            .join(Port, IP.id == Port.ip_id)
            .filter(IP.project_id == project_id)
            .group_by(
                Port.port,
                Port.protocol,
                IP.ip,
                Port.state,
                Port.service_name,
            )
            .order_by(func.count(Port.port).desc())
        )

        result = await self._session.exec(tabulator_dashboard_data)
        return result.all()