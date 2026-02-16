import aiohttp


class IpInfo:

    __allowed_fields = {
        'as', 'isp', 'lat', 'lon', 'org', 'zip', 'city',
        'proxy', 'query', 'asname', 'mobile', 'offset',
        'region', 'status', 'country', 'hosting', 'message',
        'reverse', 'currency', 'district', 'timezone',
        'continent', 'regionName', 'countryCode', 'continentCode'
    }


    @classmethod
    async def get_json(cls, target: str, fields: list[str]) -> dict:
        filtered_fields = set(fields) & cls.__allowed_fields
        api_url = f"http://ip-api.com/json/{target}?fields={','.join(filtered_fields)}"
        result = {}
        async with aiohttp.ClientSession() as cs:
            async with cs.get(api_url) as resp:
                result["X-Rl"] = int(resp.headers.get("X-Rl", '0'))       # count remaining requests
                result["X-Ttl"] = int(resp.headers.get("X-Ttl", '60'))    # seconds until reset
                if resp.status == 200:
                    result["data"] = await resp.json()
                else:
                    result["data"] = ""
        return result


