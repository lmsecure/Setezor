import aiohttp
from .models import MacVendor

class DataCollector:
    url = "http://standards-oui.ieee.org/oui.txt"

    async def _data_loader(self) -> bytes:
        async with aiohttp.ClientSession() as client_session:
            async with client_session.get(self.url) as response:
                return await response.content.read()

    def _data_parser(self, data: bytes):
        result = []
        data_list = data.splitlines()
        for index, line in enumerate(data_list):
            if b"(base 16)" in line:
                prefix, vendor = (i.strip().decode() for i in line.split(b"(base 16)", 1))
                address = ' '.join([l.strip().decode() for l in data_list[index+1:index+4]])
                result.append(MacVendor(mac_prefix=prefix, vendor=vendor, address=address))
        return result

    @classmethod
    async def get_data(cls) -> list:
        data = await cls()._data_loader()
        if not data:
            raise Exception('failed to load data')
        result = cls()._data_parser(data=data)
        return result
