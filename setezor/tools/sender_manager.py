import aiohttp
from abc import ABC, abstractmethod

from setezor.logger import logger


class SenderInterface(ABC):

    @classmethod
    @abstractmethod
    async def send_json(cls, url: str, data: dict | list[dict], timeout: float = None):
        pass


class HTTPManager(SenderInterface):
    @classmethod  # метод сервера и агента на отправку следующему звену
    async def send_json(cls, url: str, data: dict | list[dict], timeout: float = None):
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            try:
                async with session.post(url, json=data, ssl=False) as resp:
                    resp_data = await resp.json()
                    if resp.status >= 300:
                        logger.warning(f'Failed to send json | url: {url}, data: {data} | '
                                       f'Response: status code: {resp.status}, resp_data: {resp_data}')
                    else:
                        logger.debug(f'Success to send json | url: {url}, data: {data}')

                    return resp_data, resp.status
            except (aiohttp.client_exceptions.ClientConnectorError, 
                    aiohttp.client_exceptions.ContentTypeError, 
                    aiohttp.client_exceptions.InvalidUrlClientError,
                    ):
                logger.error(f'Failed to send json | url: {url}, data: {data}', exc_info=False)
                return None, 400