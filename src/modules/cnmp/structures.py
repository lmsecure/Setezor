from typing import Any
import re
from dataclasses import dataclass, field
from typing import TypeVar, Generic
from abc import ABC, abstractclassmethod

T = TypeVar('T')

class DictParsable(ABC, Generic[T]):
    
    @classmethod
    @abstractclassmethod
    def from_dict(cls, data: dict) -> T:
        ...
    
    @classmethod
    def extract_elem(cls, data: list[dict]):
        result = {}
        for i in data:
            result[i['@key']] = i.get('#text')
        return result
            

@dataclass(slots=True)
class SnmpInfo(DictParsable):
    
    enterprise: str | None = None
    engine_id_format: str | None = None
    engine_id_data: str | None = None
    snmp_engine_boots: int | None = None
    snmp_engine_time: str | None = None
    
    @classmethod
    def from_dict(cls, data: dict):
        elem = cls.extract_elem(data['elem'])
        return SnmpInfo(enterprise=elem.get('enterprise'),
                        engine_id_data=elem.get('engineIDData'),
                        engine_id_format=elem.get('engineIDFormat'),
                        snmp_engine_boots=int(elem.get('snmpEngineBoots')),
                        snmp_engine_time=elem.get('snmpEngineTime')
                        )

@dataclass(slots=True)
class Interface:
    
    iface: str | None = None
    ip: str | None = None
    netmask: str | None = None
    mac: str | None = None
    device: str | None = None
    device_type: str | None = None
    speed: str | None = None
    sent: str | None = None
    received: str | None = None
    
    @classmethod
    def __extract_value(cls, reg: str, text: str, default: Any = None):
        value = re.search(reg, text, flags=re.M)
        if value:
            groups = value.groups()
            if len(groups) > 1:
                return groups
            else:
                return groups[0]
        else:
            return default
    
    @classmethod
    def from_parts(cls, data: list[str]):
        iface = data[0]
        default = (None, None)
        data = '\n'.join(data[1:])
        mac, device = cls.__extract_value('^MAC address: (.+?) (.+?)$', data, default)
        ip, netmask = cls.__extract_value('^IP address: (.+?) Netmask: (.+?)$', data, default)
        device_type, speed = cls.__extract_value('^Type: (.+?)  Speed: (.+?)$', data, default)
        sent, received = cls.__extract_value('^Traffic stats: (.+?) sent, (.+?) received$', data, default)
            
        return Interface(
            iface=iface,
            ip=ip,
            netmask=netmask,
            mac=mac,
            device=device,
            device_type=device_type,
            speed=speed,
            sent=sent,
            received=received
        )
        
    
@dataclass(slots=True)
class SnmpInterfaces(DictParsable):
    
    interfaces: list[Interface] = field(default_factory=list)
    
    @classmethod
    def __split_to_parts(cls, data: str):
        parts = []
        tmp = []
        for i in data.split('\n'):
            if re.search('^  [^ ][^ ].+?', i):
                if tmp:
                    parts.append(tmp.copy())
                    tmp.clear()
            i = i.strip()
            if i:
                tmp.append(i)
            
        parts.append(tmp)
        return parts
    
    @classmethod
    def from_dict(cls, data: dict):
        data: str = data['@output']
        parts = cls.__split_to_parts(data)
        ifaces = [Interface.from_parts(i) for i in parts]
        return cls(ifaces)
    
@dataclass(slots=True)
class Netstat:
    
    protocol: str
    ip: str
    port: str
    map: str # Что это?
    
@dataclass(slots=True)
class SnmpNetstat(DictParsable):
    
    net_stats: list[Netstat] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict):
        
        output = data['@output']
        lines = [i for i in (line.strip() for line in output.split('\n')) if i]
        result = []
        for line in lines:
            res = [i for i in line.split(' ') if i]
            protocol = res[0]
            ip, port = res[1].split(':')
            data_map = res[2]
            result.append(Netstat(protocol, ip, port, data_map))
        return SnmpNetstat(result)
            
 
@dataclass(slots=True)                     
class Process:
    
    name: str | None = None
    path: str | None = None
    params: str | None = None
     

@dataclass(slots=True)
class SnmpProcesses(DictParsable):
    
    processes: list[Process] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict):
        
        table= data['table']
        processes = []
        for i in table:
            res = cls.extract_elem(i['elem'])
            processes.append(Process(name=res.get('Name'),
                                     path=res.get('Path'),
                                     params=res.get('Params')))
        return cls(processes)
    
@dataclass(slots=True)
class SnmpSysDescriptions(DictParsable):
    
    system: str | None = None
    uptime: str | None = None
    
    @classmethod
    def from_dict(self, data: dict):
        
        output: str = data['@output']
        lines = output.split('\n')
        try:
            system = lines[0].strip()
        except KeyError:
            system = None
        
        try:
            uptime = lines[1].strip()
        except KeyError:
            uptime = None
            
        return SnmpSysDescriptions(system, uptime)