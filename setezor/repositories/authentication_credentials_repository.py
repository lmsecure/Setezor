
from setezor.repositories import SQLAlchemyRepository
from setezor.models import Authentication_Credentials, Port, IP, Domain, DNS_A

from sqlmodel import select



class AuthenticationCredentialsRepository(SQLAlchemyRepository[Authentication_Credentials]):

    model = Authentication_Credentials

    async def exists(self, auth_obj: Authentication_Credentials):
        stmt = select(Authentication_Credentials).filter(Authentication_Credentials.project_id == auth_obj.project_id,
                                                            Authentication_Credentials.scan_id == auth_obj.scan_id,
                                                            Authentication_Credentials.port_id == auth_obj.port_id,
                                                            Authentication_Credentials.login == auth_obj.login,
                                                            Authentication_Credentials.password == auth_obj.password,
                                                            Authentication_Credentials.permissions == auth_obj.permissions,
                                                            Authentication_Credentials.need_auth == auth_obj.need_auth,
                                                            Authentication_Credentials.role == auth_obj.role)
        result = await self._session.exec(stmt)
        return result.first()

    async def get_data_for_tabulator(self, project_id: str, last_scan_id: str):
        stmt = select(IP, Domain, Port, Authentication_Credentials).select_from(Port).\
                join(Authentication_Credentials, Port.id == Authentication_Credentials.port_id).\
                join(IP, IP.id == Port.ip_id).\
                join(DNS_A, DNS_A.target_ip_id == IP.id).\
                join(Domain, Domain.id == DNS_A.target_domain_id).\
                filter(Port.project_id == project_id, Port.scan_id == last_scan_id)
        result = await self._session.exec(stmt)
        return result.all()