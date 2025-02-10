from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import AuthLog


class Auth_Log_Service(IService):
    @classmethod
    async def log_event(cls, uow: UnitOfWork, login:str, event: str):
        async with uow:
            event = AuthLog(login=login, event=event)
            uow.auth_log.add(event.model_dump())
            await uow.commit()