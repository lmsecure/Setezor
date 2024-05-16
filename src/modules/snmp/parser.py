from pydantic import BaseModel, Field, AliasChoices
import xmltodict

from .structures import (
    DictParsable,
    SnmpSysDescriptions,
    SnmpProcesses,
    SnmpInfo,
    SnmpInterfaces,
    SnmpNetstat,
)

MAP_STRUCTURE: dict[str, DictParsable] = {
    "snmp-info": SnmpInfo,
    "snmp-interfaces": SnmpInterfaces,
    "snmp-netstat": SnmpNetstat,
    "snmp-processes": SnmpProcesses,
    "snmp-sysdescr": SnmpSysDescriptions,
}


class NmapSnmpParseResult(BaseModel):
    snmp_info: SnmpInfo | None = Field(
        default=None, validation_alias=AliasChoices("snmp_info", "snmp-info")
    )
    snmp_interfaces: SnmpInterfaces = Field(
        default=None,
        validation_alias=AliasChoices("snmp_interfaces", "snmp-interfaces"),
    )
    snmp_netstat: SnmpNetstat = Field(
        default=None, validation_alias=AliasChoices("snmp_netstat", "snmp-netstat")
    )
    snmp_processes: SnmpProcesses = Field(
        default=None, validation_alias=AliasChoices("snmp_processes", "snmp-processes")
    )
    snmp_sysdescr: SnmpSysDescriptions = Field(
        default=None, validation_alias=AliasChoices("snmp_sysdescr", "snmp-sysdescr")
    )


class NmanSnmpParser:
    """Парсер вывода snmp-info"""

    def _parse_xml(self, xml_data: str):
        return xmltodict.parse(xml_data)

    def __parse_port(self, port_data: dict):
        if port_data["state"]["@state"] == "closed":
            return
        script = port_data["script"]
        if isinstance(script, dict):
            script = [script]
        map_result = {}
        for i in script:
            name = i["@id"]
            cls = MAP_STRUCTURE.get(name)
            if cls:
                obj = cls.from_dict(i)
                map_result[name] = obj
        return map_result

    def parse(self, xml_data: str | dict):
        """
        Функция парсинга xml

        :param xml_data: может быть строкой или словарем
        :return: Список pydantic моделей
        """
        if isinstance(xml_data, str):
            xml_data = self._parse_xml(xml_data)
        elif isinstance(xml_data, dict):
            pass
        else:
            raise ValueError(f"Xml data must be str or dict type is {type(xml_data)}")
        ports = xml_data["nmaprun"]["host"]["ports"]["port"]
        if isinstance(ports, dict):
            ports = [ports]
        res = (i for i in (self.__parse_port(port) for port in ports) if i)
        res = [NmapSnmpParseResult.model_validate(i) for i in res]
        return res
