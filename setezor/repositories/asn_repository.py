from setezor.models import ASN
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select

class ASN_Repository(SQLAlchemyRepository[ASN]):
    model = ASN


    async def exists(self, asn_obj: ASN):
        if not asn_obj.project_id or not asn_obj.scan_id:
            return
        stmt = select(ASN).filter(ASN.project_id == asn_obj.project_id, ASN.scan_id == ASN.scan_id,
                                  ASN.number == asn_obj.number, ASN.name == asn_obj.name,
                                  ASN.org == asn_obj.org, ASN.isp == asn_obj.isp,
                                  ASN.proxy == asn_obj.proxy, ASN.hosting == asn_obj.hosting,
                                  ASN.country == asn_obj.country, ASN.city == asn_obj.city)
        result = await self._session.exec(stmt)
        result_obj = result.first()
        return result_obj
