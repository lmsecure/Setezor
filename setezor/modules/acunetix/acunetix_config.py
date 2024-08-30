
import json
import aiofiles
from .utils import send_request


class Config:
    @classmethod
    async def get(cls, path: str):
        async with aiofiles.open(path, 'r') as file:
            raw_data = await file.read()
            if not raw_data:
                return {}
            return json.loads(raw_data)

    @classmethod
    async def health_check(cls, credentials: dict):
        params = {"l": 1}
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url="/api/v1/target_groups",
                                  method="GET",
                                  params=params)

    @classmethod
    async def set(cls, path: str, payload: dict):
        async with aiofiles.open(path, 'w') as file:
            await file.write(payload)
