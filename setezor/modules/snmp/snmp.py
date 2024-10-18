import os
import asyncio
import aiofiles

from pysnmp.hlapi.v3arch.asyncio import *





class SNMP:

    @classmethod
    async def get(cls, ip_address: str, community_string: str, oid: str):
        get_request = await getCmd(SnmpEngine(),
                                CommunityData(community_string),
                                await UdpTransportTarget.create((ip_address, 161), timeout=0.5),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid)))
        return get_request

    def get_new_var(self, value):
        if isinstance(value, str):
            return OctetString(value)
        elif isinstance(value, int):
            return Integer(value)
        else:
            raise Exception("This type of data is not yet processed, please give Int or Str")
    
    def get_new_obj(self, oid, value):
        var = self.get_new_var(value)
        return ObjectType(ObjectIdentity(oid), var)

    @classmethod
    async def set(cls, ip_address: str, community_string: str, oid: str, var):
        get_result = setCmd(SnmpEngine(),
                            CommunityData(community_string),
                            await UdpTransportTarget.create((ip_address, 161)),
                            ContextData(),
                            ObjectType(ObjectIdentity(oid), var))
        return await get_result

    @classmethod
    async def is_write_access(cls, ip_address: str, community_string: str) -> bool:
        oid = '1.3.6.1.2.1.1.5.0'
        error_indication, error_status, error_index, var_binds = await cls.get(ip_address=ip_address, community_string=community_string, oid=oid)
        if error_indication:
            raise Exception(str(error_indication))
        error_indication, error_status, error_index, var_binds = await cls.set(ip_address=ip_address, community_string=community_string, oid=oid, var=var_binds[0][1])
        if error_status:
            return False
        return True

    @classmethod
    async def _walk(cls, ip_address: str, community_string: str):
        get_result = walkCmd(SnmpEngine(),
                             CommunityData(community_string),
                             await UdpTransportTarget.create((ip_address, 161)),
                             ContextData(),
                             ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr')))
        async for item in get_result:
            yield item

    @classmethod
    async def walk(cls, ip_address: str, community_string: str) -> list:
        result = []
        async for item in cls._walk(ip_address=ip_address, community_string=community_string):
            error_indication, error_status, error_index, var_binds = item
            if not error_indication:
                result.append([str(var_binds[0][0]), type(var_binds[0][1]), str(var_binds[0][1])])
        return result


class SNMP_brute:

    @classmethod
    async def _brute_community_string(cls, ip_address: str, community_string : str, oid: str) -> tuple[bool, str, str | None]:
        error_indication, error_status, error_index, var_binds = await SNMP.get(ip_address = ip_address, community_string = community_string, oid=oid)
        return not error_indication, community_string, error_status.prettyOut(error_status) if error_status else None

    @classmethod
    async def community_string(cls, ip_address: str, community_strings: list = None) -> list[tuple[bool, str, str | None]]:
        if not community_strings:
            path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "default_dict.txt")
            async with aiofiles.open(path, 'r') as csf:
                community_strings = (await csf.read()).splitlines()
        oid = '1.3.6.1.2.1.1.1.0'
        tasks = []
        for community_string in community_strings:
            tasks.append(asyncio.create_task(cls._brute_community_string(ip_address=ip_address, community_string=community_string, oid=oid)))
        return list(filter(lambda x: x[0], await asyncio.gather(*tasks)))
    



