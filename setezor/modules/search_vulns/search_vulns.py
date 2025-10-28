import aiohttp
import json
import os
from setezor.logger import logger

API = os.environ.get("SEARCH_VULNS_API", "https://search-vulns.com")

class SearchVulns:
    @classmethod
    async def find(cls, token: str, query_string: str):
        headers = {'API-Key': token}
        params = {"query": query_string}
        async with aiohttp.ClientSession() as ses:
            try:
                async with ses.get(f"{API}/api/search-vulns", headers=headers, params=params) as resp:
                    if resp.status != 200:
                        return {}
                    return await resp.json()
            except aiohttp.client_exceptions.ServerDisconnectedError:
                return {}
            except Exception as e:
                logger.error(e)
                return {}

    @classmethod
    async def check_token(cls, token: str):
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({"key": token})
        async with aiohttp.ClientSession() as ses:
            async with ses.post(f"{API}/api/check-key-status", data=data, headers=headers) as resp:
                if resp.status >= 500:
                    return True
                result = await resp.json()
        if result.get("status") == "valid":
            return True
        return False
