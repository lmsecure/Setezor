import asyncio

from pysnmp.hlapi.v3arch.asyncio import *
from pysnmp.smi import builder, view, compiler

from concurrent.futures import ThreadPoolExecutor


class SNMP:

    @classmethod
    async def get(cls, ip_address: str, port: int, community_string: str, oid: str):
        get_request = await getCmd(SnmpEngine(),
                                CommunityData(community_string),
                                await UdpTransportTarget.create((ip_address, port)),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid)))
        return get_request

    @classmethod
    async def get_value(cls, ip_address: str, port: int, community_string: str, oid: str):
        error_indication, error_status, error_index, var_binds = await cls.get(ip_address=ip_address, port=port, community_string=community_string, oid=oid)
        if error_indication:
            raise Exception(error_indication)
        else:
            if var_binds[0][1].prettyPrint() == "No Such Object currently exists at this OID":
                raise Exception("No Such Object currently exists at this OID", oid, ip_address, port, community_string)
            return var_binds[0][1]

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
    async def set(cls, ip_address: str, port: int, community_string: str, oid: str, var):
        get_result = setCmd(SnmpEngine(),
                            CommunityData(community_string),
                            await UdpTransportTarget.create((ip_address, port)),
                            ContextData(),
                            ObjectType(ObjectIdentity(oid), var))
        return await get_result

    @classmethod
    async def set_value(cls, ip_address: str, port: int, community_string: str, oid: str, value):
        new_var = SNMP.get_new_var(cls, value)
        error_indication, error_status, error_index, var_binds = await cls.set(ip_address=ip_address, port=port, community_string=community_string, oid=oid, var=new_var)
        if error_indication:
            raise Exception(error_indication)
        else:
            return var_binds[0][1]

    @classmethod
    async def _walk(cls, ip_address: str, port: int, community_string: str, oid: str, limit: int = 0):
        ObjID = ObjectIdentity(oid)
        get_result = walkCmd(SnmpEngine(),
                             CommunityData(community_string),
                             await UdpTransportTarget.create((ip_address, port)),
                             ContextData(),
                             ObjectType(ObjID),
                             maxCalls = limit) # ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr'))    ObjectType(ObjID)
        async for item in get_result:
            error_indication, error_status, error_index, var_binds = item
            yield item

    @classmethod
    async def walk(cls, ip_address: str, port: int, community_string: str, oid: str, limit: int = 0) -> list:
        result = []
        async for item in cls._walk(ip_address=ip_address, port=port, community_string=community_string, oid=oid, limit=limit):
            error_indication, error_status, error_index, var_binds = item
            if not error_indication:
                result.append(var_binds[0][1])
        return result
    

    @classmethod
    async def get_block(cls, ip_address: str, port: int, community_string: str, oid: str) -> list:
        result = []
        stop = True
        next_oid = oid
        while stop:
            error_indication, error_status, error_index, var_binds = await bulkCmd(SnmpEngine(),
                                                                                   CommunityData( community_string),
                                                                                   await UdpTransportTarget.create((ip_address, port)),
                                                                                   ContextData(),
                                                                                   0, 1,
                                                                                   ObjectType( ObjectIdentity(next_oid)),
                                                                                   lexicographicMode=False)
            if error_indication:
                raise Exception(error_indication, ip_address, port, community_string, oid)
            elif error_status:
                raise Exception(error_status, ip_address, port, community_string, oid)
            else:
                for var_bind in var_binds:
                    if not str(var_bind[0]).startswith(oid):
                        stop = False
                        break
                    result.append(var_bind[1].prettyPrint())
                    next_oid = str(var_bind[0])
        return result


class SnmpGettingAccess(SNMP):

    @classmethod
    def _brute_community_string(cls, ip_address: str, port: int, community_string : str, oid: str) -> tuple[bool, str, str | None]:
        loop = asyncio.get_event_loop()
        loop.set_default_executor(ThreadPoolExecutor(max_workers=250))
        error_indication, error_status, error_index, var_binds = loop.run_until_complete(cls.get(ip_address = ip_address, port=port, community_string = community_string, oid=oid))
        return not error_indication, community_string, error_status.prettyOut(error_status) if error_status else None

    @classmethod
    async def community_string(cls, ip_address: str, port: int, community_strings: list = None) -> list[tuple[bool, str, str | None]]:
        if not community_strings: community_strings = ["public", "private"]
        oid = '1.3.6.1.2.1.1.1.0'
        tasks = []
        for community_string in community_strings:
            tasks.append(asyncio.to_thread(cls._brute_community_string, ip_address, port, community_string, oid))
        return list(filter(lambda x: x[0], await asyncio.gather(*tasks)))

    @classmethod
    async def is_write_access(cls, ip_address: str, port: int, community_string: str) -> bool:
        oid = '1.3.6.1.2.1.1.5.0'
        error_indication, error_status, error_index, var_binds = await cls.get(ip_address=ip_address, port=port, community_string=community_string, oid=oid)
        if error_indication:
            raise Exception(str(error_indication))
        error_indication, error_status, error_index, var_binds = await cls.set(ip_address=ip_address, port=port, community_string=community_string, oid=oid, var=var_binds[0][1])
        if error_status:
            return False
        return True





class SnmpGet(SNMP):
    """Class for obtaining data on specific oids.

    Methods:
        system_name
        number_of_interfaces
        interface_description
        phys_address
    """
    def __init__(self, ip_address: str, port: int, community_string: str, ifnumber: int):
        self.ip_address = ip_address
        self.port = port
        self.community_string = community_string
        self.ifnumber = ifnumber

    @classmethod
    async def create_obj(cls, ip_address: str, port: int, community_string: str):
        ifnumber = await cls.number_of_interfaces(ip_address=ip_address, port=port, community_string=community_string)
        return cls(ip_address=ip_address, port=port, community_string=community_string, ifnumber=ifnumber)

    @classmethod
    async def number_of_interfaces(cls, ip_address: str, port: int, community_string: str) -> int:
        """The number of network interfaces (regardless of their
            current state) present on this system.

        Args:
            ip_address (str): ip address
            community_string (str): community string

        Returns:
            int: ifNumber
        """
        oid = "1.3.6.1.2.1.2.1.0"               # ifNumber
        result = 0
        try:
            result = int(await cls.get_value(ip_address=ip_address, port=port, community_string=community_string, oid=oid))
        finally:
            return result


    async def system_name(self) -> str:
        """An administratively-assigned name for this managed
            node.  By convention, this is the node's fully-qualified
            domain name.  If the name is unknown, the value is
            the zero-length string.

        Args:
            ip_address (str): ip address
            community_string (str): community string

        Returns:
            str: sysName
        """
        oid = "1.3.6.1.2.1.1.5.0"               # sysName
        return str(await self.get_value(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid))
    
    async def interface_index(self) -> list:
        """A unique value for each interface. Its value
            ranges between 1 and the value of ifNumber. The
            value for each interface must remain constant at
            least from one re-initialization of the entity's
            network management system to the next re-
            initialization. 

        Returns:
            list: [ifIndex]
        """

        oid = "1.3.6.1.2.1.2.2.1.1"            # ifIndex
        result = []
        for item in await self.walk(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, limit=self.ifnumber):
            result.append(str(item))
        return result

    async def interface_description(self) -> list[str]:
        """A textual string containing information about the
            interface.  This string should include the name of the
            manufacturer, the product name and the version of the
            interface hardware/software.

        Args:
            ip_address (str): ip address
            community_string (str): community string
            count (int): number of interfaces

        Returns:
            list[str]: [ifDescr]
        """
        oid = "1.3.6.1.2.1.2.2.1.2"            # ifDescr
        result = []
        for item in await self.walk(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, limit=self.ifnumber):
            result.append(str(item))
        return result

    async def phys_address(self) -> list[str]:
        """The interface's address at its protocol sub-layer.  For
            example, for an 802.x interface, this object normally
            contains a MAC address.  The interface's media-specific MIB
            must define the bit and byte ordering and the format of the
            value of this object.  For interfaces which do not have such
            an address (e.g., a serial line), this object should contain
            an octet string of zero length.

        Args:
            ip_address (str): ip address
            community_string (str): community string
            count (int): number of interfaces

        Returns:
            list[str]: [ifPhysAddress]
        """
        oid = "1.3.6.1.2.1.2.2.1.6"     # .ifPhysAddress
        result = []
        for tmp in await self.walk(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, limit=self.ifnumber):
            result.append(':'.join([tmp.prettyPrint()[2:][i:i+2].upper() for i in range(0, len(tmp.prettyPrint()[2:]), 2)]))
        return result

    async def ip_add_ent_addr(self) -> list[str]:
        """The IP address to which this entry's addressing
            information pertains. 

        Returns:
            list[str]: [ipAdEntAddr]
        """
        oid = "1.3.6.1.2.1.4.20.1.1"            # ipAdEntAddr
        result = await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid)
        return result

    async def ip_add_ent_if_ind(self) -> list:
        """The index value which uniquely identifies the interface to
            which this entry is applicable. The interface identified by
            a particular value of this index is the same interface as
            identified by the same value of the IF-MIB's ifIndex.

        Returns:
            list: [ipAdEntIfIndex]
        """
        oid = "1.3.6.1.2.1.4.20.1.2"            # ipAdEntIfIndex
        result = await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid)
        return result



    async def udp(self):
        oid = "1.3.6.1.2.1.7" # udp
        oid = "1.3.6.1.2.1.7.1.1" # ip's
        oid = "1.3.6.1.2.1.7.1.2" # port's

        ...












    @classmethod
    def ObjId(cls):
        mib_builder = builder.MibBuilder()
        mib_view = view.MibViewController(mib_builder)

        # q = ObjectIdentity('1')
        # q.prettyPrint

        obj_ids = []
        obj_ids.append(ObjectIdentity('SNMPv2-MIB', 'sysDescr'))
        obj_ids.append(ObjectIdentity(None, 'sysName'))
        obj_ids.append(ObjectIdentity(None, 'iso'))
        obj_ids.append(ObjectIdentity('1.3.6.1.2.1.2.2.1.6')) # iso.org.dod.internet.mgmt.mib-2.interfaces.ifTable.ifEntry.ifPhysAddress
        obj_ids.append(ObjectIdentity(None, 'mib-2'))


        for obj_id in obj_ids:
            obj_id.resolveWithMib(mib_view)
            print(obj_id.getLabel(), obj_id.getOid())

        return obj_ids