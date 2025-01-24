from abc import ABC, abstractmethod


class IService(ABC):
    @abstractmethod
    async def list():
        raise NotImplementedError

    @abstractmethod
    async def get():
        raise NotImplementedError

    @abstractmethod
    async def create():
        raise NotImplementedError
