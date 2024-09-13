
import json
import aiofiles
from .utils import send_request


class Config:
    @classmethod
    async def get(cls, path: str, name: str | None = None, any_config : bool = True):
        async with aiofiles.open(path, 'r') as file:
            raw_data = await file.read()
        if not raw_data:
            return {}
        instances = json.loads(raw_data)
        if any_config:
            for cred in instances.values():
                return cred
        if name:
            return instances[name]
        return instances

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
        async with aiofiles.open(path, 'r') as file:
            raw_instances = await file.read()
        try:
            current_instances = json.loads(raw_instances)
        except:
            current_instances = {}
        current_instances[payload.pop("name")] = payload
        async with aiofiles.open(path, 'w') as file:
            await file.write(json.dumps(current_instances,indent=4))
