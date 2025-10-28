from setezor.models import Network
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select

class NetworkRepository(SQLAlchemyRepository[Network]):
    model = Network


    async def exists(self, network_obj: Network):
        stmt = select(Network).filter(Network.start_ip == network_obj.start_ip, 
                                      Network.mask == network_obj.mask, 
                                      Network.parent_network == network_obj.parent_network, 
                                      Network.project_id == network_obj.project_id,
                                      Network.scan_id==network_obj.scan_id
                                      )
        result = await self._session.exec(stmt)
        result_obj = result.first()
        return result_obj