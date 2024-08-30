import asyncio
from typing import Union
from .utils import send_request
from .schemes.group import Group as GroupScheme
from .target import Target


class Group:
    url = "/api/v1/target_groups"

    @classmethod
    async def get_all(cls, params: dict, credentials: dict) -> Union[list[GroupScheme], int]:
        raw_data = await send_request(base_url=credentials["url"],
                                      token=credentials["token"],
                                      url="/api/v1/target_groups",
                                      method="GET",
                                      params=params)
        if raw_data.get("code"):
            return {}
        groups: list[GroupScheme] = raw_data.get("groups")
        for group in groups:
            resp = await send_request(base_url=credentials["url"],
                                      token=credentials["token"],
                                      url=f"{
                                          cls.url}/{group['group_id']}/targets",
                                      method="GET")
            targets_ids = resp['target_id_list']
            tasks = []
            for target_id in targets_ids:
                task = asyncio.create_task(Target.get_by_id(
                    id=target_id, credentials=credentials))
                tasks.append(task)
            targets = await asyncio.gather(*tasks)
            group["targets"] = "\n".join(
                [target['address'] for target in targets])
        pagination = raw_data.get("pagination")
        count = pagination.get("count")
        return groups, count

    @classmethod
    async def get_targets(cls, id: str, credentials: dict):
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=f"{cls.url}/{id}/targets",
                                  method="GET")

    @classmethod
    async def create(cls, payload: dict, credentials: dict) -> Union[int, str]:
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=cls.url,
                                  method="POST",
                                  data=payload)
