from setezor.services.base_service import BaseService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import AuthLog


class Auth_Log_Service(BaseService):
    async def log_event(self, login:str, event: str):
        async with self._uow:
            event = AuthLog(login=login, event=event)
            self._uow.auth_log.add(event.model_dump())
            await self._uow.commit()