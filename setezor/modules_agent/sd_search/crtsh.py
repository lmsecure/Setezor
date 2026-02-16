import aiohttp
class CrtSh:
    @staticmethod
    async def crt_sh(domain:str):
        # logger.debug('Start crt.sh [%s] ', domain)
        url = f'https://crt.sh/?q={domain}&output=json'
        result = set()
        async with aiohttp.ClientSession() as session:  
            async with session.get(url) as response:
                if response.status != 200 or response.headers['content-type'] != 'application/json':
                    raise ValueError('Invalid response from crt.sh')
                records = await response.json()
                for record in records:
                    names = record.get("name_value").split("\n")
                    for name in names:
                        if not "*" in name:
                            result.add(name)
        return list(result)