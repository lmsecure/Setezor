import aiohttp
from abc import ABC, abstractmethod


class SenderInterface(ABC):
    @abstractmethod
    async def send_bytes():
        pass

    @abstractmethod
    async def send_json():
        pass


class HTTPManager(SenderInterface):
    @classmethod  # метод агента на отправку результата на предыдущего агента
    async def send_bytes(cls, url: str, data: bytes):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data, ssl=False) as resp:
                    return await resp.read()
            except aiohttp.client_exceptions.ClientConnectorError as e:
                return e

    @classmethod  # метод сервера и агента на отправку следующему звену
    async def send_json(cls, url: str, data: dict | list[dict]):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data, ssl=False) as resp:
                    return resp.status
            except aiohttp.client_exceptions.ClientConnectorError as e:
                return 0