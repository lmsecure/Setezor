
from setezor.repositories import SQLAlchemyRepository
from setezor.models import L7_Authentication_Credentials, L7, Port, IP, Domain

from sqlmodel import select



class L7AuthenticationCredentialsRepository(SQLAlchemyRepository[L7_Authentication_Credentials]):

    model = L7_Authentication_Credentials

    async def exists(self, auth_obj: L7_Authentication_Credentials):
        stmt = select(L7_Authentication_Credentials).filter(L7_Authentication_Credentials.project_id == auth_obj.project_id,
                                                            L7_Authentication_Credentials.scan_id == auth_obj.scan_id,
                                                            L7_Authentication_Credentials.l7_id == auth_obj.l7_id,
                                                            L7_Authentication_Credentials.login == auth_obj.login,
                                                            L7_Authentication_Credentials.password == auth_obj.password,
                                                            L7_Authentication_Credentials.permissions == auth_obj.permissions,
                                                            L7_Authentication_Credentials.need_auth == auth_obj.need_auth,
                                                            L7_Authentication_Credentials.role == auth_obj.role)
        result = await self._session.exec(stmt)
        return result.first()

    async def get_data_for_tabulator(self, project_id: str):
        stmt = select(IP, Domain, Port, L7_Authentication_Credentials).select_from(L7).\
                join(L7_Authentication_Credentials, L7.id == L7_Authentication_Credentials.l7_id).\
                join(Domain, Domain.id == L7.domain_id).\
                join(Port, Port.id == L7.port_id).\
                join(IP, IP.id == Port.ip_id).\
                filter(L7.project_id == project_id)
        result = await self._session.exec(stmt)
        return result.all()