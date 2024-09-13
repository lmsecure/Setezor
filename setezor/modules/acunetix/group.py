import asyncio
from typing import Union
from .utils import send_request
from .schemes.group import Group as GroupScheme
from .target import Target
import json


class Group:
    url = "/api/v1/target_groups"

    @classmethod
    async def get_all(cls, credentials: dict) -> Union[list[GroupScheme], int]:
        params = {"l": 100, "c": 0}
        raw_data = await send_request(base_url=credentials["url"],
                                      token=credentials["token"],
                                      url=cls.url,
                                      method="GET",
                                      params=params)
        if raw_data.get("code"):
            return {}
        groups: list[GroupScheme] = raw_data.get("groups")
        while True:
            params["c"] += 100
            raw_data = await send_request(base_url=credentials["url"],
                                          token=credentials["token"],
                                          url=cls.url,
                                          method="GET",
                                          params=params)
            raw_groups = raw_data.get("groups")
            if not raw_groups:
                break
            groups.extend(raw_groups)
        return groups

    @classmethod
    async def get_targets(cls, id: str, credentials: dict):
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=f"{cls.url}/{id}/targets",
                                  method="GET")

    @classmethod
    async def set_targets(cls, id: str, payload: dict, credentials: dict):
        new_targets = set(payload.get('new_targets'))
        raw_data = await cls.get_targets(id=id, credentials=credentials)
        current_targets = set(raw_data.get('target_id_list'))
        for_delete = current_targets.difference(new_targets)
        for_add = new_targets.difference(current_targets)
        data = json.dumps({
            "add": list(for_add),
            "remove": list(for_delete)
        })
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=f"{cls.url}/{id}/targets",
                                  method="PATCH",
                                  data=data)

    @classmethod
    async def create(cls, payload: dict, credentials: dict) -> Union[int, str]:
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=cls.url,
                                  method="POST",
                                  data=payload)

    @classmethod
    async def set_targets_proxy(cls, id: str, payload: dict, credentials: dict):
        raw_data = await cls.get_targets(id=id, credentials=credentials)
        target_ids = raw_data.get("target_id_list")
        for target_id in target_ids:
            await Target.set_proxy(id=target_id, payload=payload, credentials=credentials)
        return 204
