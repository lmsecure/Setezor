
import xmltodict

from .structures import (
    DictParsable,
    SnmpSysDescriptions,
    SnmpProcesses,
    SnmpInfo,
    SnmpInterfaces,
    SnmpNetstat
)

MAP_STRUCTURE: dict[str,DictParsable] = {
    'snmp-info': SnmpInfo,
    'snmp-interfaces': SnmpInterfaces,
    'snmp-netstat': SnmpNetstat,
    'snmp-processes': SnmpProcesses,
    'snmp-sysdescr': SnmpSysDescriptions
}

class NmanSnmpParser:
    
    """Парсер вывода snmp-info"""
    
    def _parse_xml(self, xml_data: str):
        return xmltodict.parse(xml_data)
    
    def _parse_port(self, port_data: dict):
        if port_data['state']['@state'] == 'closed':
            return
        script = port_data['script']
        map_result= {}
        for i in script:
            name = i['@id']
            cls = MAP_STRUCTURE[name]
            obj = cls.from_dict(i)
            map_result[name] = obj
        return map_result
            
    
    def get_result(self, xml_data: str):
    
        data = self._parse_xml(xml_data)
        ports = data['nmaprun']['host']['ports']['port']
        if isinstance(ports, dict):
            ports = [ports]
        
        res = [i for i in (self._parse_port(port) for port in ports) if i]
        return res
        