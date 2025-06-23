
from sqlalchemy.orm import aliased
from requests import session
from sqlalchemy import Select, desc, text
from sqlmodel import select, func, or_, and_
from setezor.models import SoftwareVersion, Software, SoftwareType, Port, Vendor
from setezor.models.l4_software import L4Software
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class SoftwareRepository(SQLAlchemyRepository[Software]):
    model = Software


    async def list(self):
        stmt = select(Software, Vendor, SoftwareVersion)\
        .join(Vendor, Software.vendor_id == Vendor.id)\
        .join(SoftwareVersion, SoftwareVersion.software_id == Software.id)\
        .filter(Software.product != "")
        res = await self._session.exec(stmt)
        return res.all()


    async def exists(self, software_obj: Software):
        dct = software_obj.model_dump()
        filtered_keys = {k:v for k, v in dct.items() if v is not None}
        if not filtered_keys: return False
        stmt = select(Software).filter_by(**filtered_keys)
        res = await self._session.exec(stmt)
        return res.first()


    async def get_software_version_cpe(self, project_id: str, last_scan_id: str):

        """Считает количество сток"""
        query = (
        select(
            Software.product,
            SoftwareVersion.version,
            SoftwareVersion.cpe23,
            func.count(SoftwareVersion.cpe23).label('qty')
        ).join(SoftwareVersion, Software.id == SoftwareVersion.software_id)\
        .join(L4Software, L4Software.software_version_id == SoftwareVersion.id)\
        .filter(L4Software.project_id == project_id, L4Software.scan_id == last_scan_id)\
        .filter(SoftwareVersion.cpe23.is_not(None))\
        .group_by(SoftwareVersion.cpe23, Software.product, SoftwareVersion.version)\
        .order_by(func.count(SoftwareVersion.cpe23).desc())\
        )

        result = await self._session.exec(query)
        software_version_cpe = result.fetchall()

        return software_version_cpe

    async def get_top_products(self, project_id: str, last_scan_id: str):
        top_products: Select = select(
            Software.product, 
            func.count(Software.product).label("count")
        ).join(SoftwareVersion, Software.id == SoftwareVersion.software_id)\
        .join(L4Software, L4Software.software_version_id == SoftwareVersion.id)\
        .filter(L4Software.project_id == project_id, L4Software.scan_id == last_scan_id)\
        .filter(Software.product != None)\
        .filter(Software.product != "")\
        .group_by(Software.product)\
        .order_by(desc("count"))\

        result = await self._session.exec(top_products)
        top_products_result = result.all()
        return top_products_result

    async def for_search_vulns(self, project_id: str, scan_id: str):

        addition = [Vendor.name != None, Software.product != None, SoftwareVersion.version != None]

        stmt_l4 = select(
            Vendor.name,
            L4Software,
            SoftwareVersion,
            Software,
            ).select_from(Port).join(L4Software, Port.id == L4Software.l4_id)\
            .join(SoftwareVersion, L4Software.software_version_id == SoftwareVersion.id)\
            .join(Software, SoftwareVersion.software_id == Software.id)\
            .join(Vendor, Software.vendor_id == Vendor.id)\
            .filter(Port.project_id == project_id, Port.scan_id == scan_id)\
            .filter(*addition)
        l4_soft_with_cpe23 = await self._session.exec(stmt_l4)
        return l4_soft_with_cpe23.all()
