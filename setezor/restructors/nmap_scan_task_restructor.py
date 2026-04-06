import asyncio
from concurrent.futures import ProcessPoolExecutor

from setezor.modules.nmap.parser import NmapParser

executor = ProcessPoolExecutor(max_workers=4)


class NmapScanTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result: str, agent_id: str, self_address: dict, interface_ip_id: str, **kwargs):
        loop = asyncio.get_running_loop()
        xml = await loop.run_in_executor(executor, NmapParser.parse_xml, raw_result)
        parse_result, traceroute = await loop.run_in_executor(executor, NmapParser().parse_hosts, xml.get('nmaprun'), agent_id, self_address)
        result = await loop.run_in_executor(executor, NmapParser.restruct_result, parse_result, interface_ip_id, traceroute)
        return result
    
    @classmethod
    def get_raw_result(cls, data):
        return data.encode()