import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

import aiohttp
from aiohttp import ClientSession


class GetAs(StrEnum):
    dict = 'dict'
    text = 'text'
    file = 'file'


@dataclass
class File:
    name: str | None
    content: bytes


class ApiClient:

    async def get(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        timeout: int = None,
        get_as: GetAs = GetAs.dict,
    ) -> Optional[dict] | Optional[File] | Optional[str]:
        async with ClientSession() as session:
            async with await session.get(
                url,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status in [200, 201, 204]:
                    if get_as == GetAs.text:
                        return await resp.text()
                    elif get_as == GetAs.file:
                        cd = resp.headers.get('Content-Disposition', '') or ''
                        m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd)
                        return File(
                            name=m.group(1) if m else None,
                            content=await resp.content.read(),
                        )
                    return await resp.json()

    async def post(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        timeout: int = None,
        get_as: GetAs = GetAs.dict,
    ) -> Optional[dict] | Optional[File] | Optional[str]:
        async with ClientSession() as session:
            async with await session.post(
                url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status in [200, 201, 204]:
                    if get_as == GetAs.text:
                        return await resp.text()
                    elif get_as == GetAs.file:
                        cd = resp.headers.get('Content-Disposition', '') or ''
                        m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd)
                        return File(
                            name=m.group(1),
                            content=await resp.read(),
                        )
                    return await resp.json()
