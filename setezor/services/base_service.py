from abc import ABC, abstractmethod
from pydantic import BaseModel
from setezor.db.uow_dependency import get_uow
from setezor.unit_of_work.unit_of_work import UnitOfWork


class BaseService:
    def __init__(self, uow: UnitOfWork):
        self._uow: UnitOfWork = uow

    @abstractmethod
    def create(self, new_object: BaseModel):
        pass

    @classmethod
    def new_instance(cls):
        return cls(uow=get_uow())
