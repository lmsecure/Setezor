from setezor.modules.nmap.parser import NmapParser

class NmapScanTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result: str, agent_id: str, self_address: dict, interface_ip_id: str, **kwargs):
        xml = NmapParser.parse_xml(raw_result)
        parse_result, traceroute = NmapParser().parse_hosts(scan=xml.get('nmaprun'), agent_id=agent_id, self_address=self_address)
        result = NmapParser.restruct_result(data=parse_result, interface_ip_id=interface_ip_id, traceroute=traceroute)
        return result
    
    @classmethod
    def get_raw_result(cls, data):
        return data.encode()