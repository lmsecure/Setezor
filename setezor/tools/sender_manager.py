import aiohttp
from abc import ABC, abstractmethod


class SenderInterface(ABC):
    @abstractmethod
    async def send_json():
        pass


class HTTPManager(SenderInterface):
    @classmethod  # метод сервера и агента на отправку следующему звену
    async def send_json(cls, url: str, data: dict | list[dict]):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data, ssl=False) as resp:
                    return await resp.json(), resp.status
            except (aiohttp.client_exceptions.ClientConnectorError, 
                    aiohttp.client_exceptions.ContentTypeError, 
                    aiohttp.client_exceptions.InvalidUrlClientError,
                    ):
                return None, 400