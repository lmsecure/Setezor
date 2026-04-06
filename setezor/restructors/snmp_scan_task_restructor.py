from setezor.modules.snmp.snmp_parser import SNMP_Parser


class SnmpTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result, target_ip: str, target_port: str, **kwargs):

        return await SNMP_Parser.restruct(raw_result=raw_result, target_ip=target_ip, target_port=target_port)
