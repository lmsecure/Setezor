from sqlmodel import select
from setezor.models import DNS_A, IP, Domain
from setezor.repositories import SQLAlchemyRepository


class DNS_A_Repository(SQLAlchemyRepository[DNS_A]):
    model = DNS_A

    async def exists(self, dns_obj: DNS_A):
        if dns_obj.target_ip_id and dns_obj.target_domain_id:
            stmt = select(DNS_A).where(DNS_A.target_ip_id == dns_obj.target_ip_id,
                                       DNS_A.target_domain_id == dns_obj.target_domain_id,
                                       DNS_A.scan_id == dns_obj.scan_id,
                                       DNS_A.project_id == dns_obj.project_id)
        elif dns_obj.target_ip_id and dns_obj.target_domain:
            stmt = select(DNS_A)\
                .join(Domain, DNS_A.target_domain_id == Domain.id)\
                .where(Domain.domain == dns_obj.target_domain.domain,
                       DNS_A.target_ip_id == dns_obj.target_ip_id,
                       DNS_A.scan_id == dns_obj.scan_id,
                       DNS_A.project_id == dns_obj.project_id)
        elif dns_obj.target_domain_id and dns_obj.target_ip:
            stmt = select(DNS_A)\
                .join(IP, DNS_A.target_ip_id == IP.id)\
                .where(IP.ip == dns_obj.target_ip.ip,
                       DNS_A.target_domain_id == dns_obj.target_domain_id,
                       DNS_A.scan_id == dns_obj.scan_id,
                       DNS_A.project_id == dns_obj.project_id)
        else:
            return
        result = await self._session.exec(stmt)
        return result.first()
