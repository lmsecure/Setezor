from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.db.database import async_session_maker

uow_factory = lambda: UnitOfWork(session_factory=async_session_maker)

def get_uow():
    return uow_factory()