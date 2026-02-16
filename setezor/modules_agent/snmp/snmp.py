import asyncio
import json

from pysnmp.hlapi.v3arch.asyncio import *



class SNMP:

    @classmethod
    async def get(cls, ip_address: str, port: int, community_string: str, oid: str, snmp_version: int = 1):
        get_request = await getCmd(SnmpEngine(),
                                CommunityData(community_string, mpModel=snmp_version),      # mpModel: 0 - for SNMP v1; 1 - for SNMP v2c
                                await UdpTransportTarget.create((ip_address, port)),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid)))
        return community_string, *get_request

    @classmethod
    async def get_value(cls, ip_address: str, port: int, community_string: str, oid: str, snmp_version: int = 1):
        community_string, error_indication, error_status, error_index, var_binds = await cls.get(ip_address=ip_address, port=port, community_string=community_string, oid=oid, snmp_version=snmp_version)
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
    async def set(cls, ip_address: str, port: int, community_string: str, oid: str, var, snmp_version: int = 1):
        get_result = setCmd(SnmpEngine(),
                            CommunityData(community_string, mpModel=snmp_version),
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
    async def get_block(cls, ip_address: str, port: int, community_string: str, oid: str, snmp_version: int = 1) -> list:
        result = []
        stop = True
        next_oid = oid
        while stop:
            error_indication, error_status, error_index, var_binds = await bulkCmd(SnmpEngine(),
                                                                                   CommunityData( community_string, mpModel=snmp_version),
                                                                                   await UdpTransportTarget.create((ip_address, port)),
                                                                                   ContextData(),
                                                                                   0, 25,
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
    async def get_community_strings_with_read_access(cls, ip_address: str, port: int, community_strings: set, snmp_version: int = 1) -> list[int, tuple[bool, str, str | None]]:
        oid = '1.3.6.1.2.1.1.1.0'
        tasks = []
        for community_string in community_strings:
            tasks.append(cls.get(ip_address=ip_address, port=port, community_string=community_string, oid=oid, snmp_version=snmp_version))
        result = []
        for item in await asyncio.gather(*tasks):
            community_string, error_indication, error_status, error_index, var_binds = item
            if not error_indication:
                result.append((snmp_version, community_string, error_status.prettyOut(error_status) if error_status else None))
        return result

    @classmethod
    async def is_write_access(cls, ip_address: str, port: int, community_string: str, snmp_version: int = 1) -> bool:
        oid = '1.3.6.1.2.1.1.5.0'
        community_string, error_indication, error_status, error_index, var_binds = await cls.get(ip_address=ip_address, port=port, community_string=community_string, oid=oid, snmp_version=snmp_version)
        if error_indication:
            raise Exception(str(error_indication))
        error_indication, error_status, error_index, var_binds = await cls.set(ip_address=ip_address, port=port, community_string=community_string, oid=oid, var=var_binds[0][1], snmp_version=snmp_version)
        if error_status:
            return False
        return True

    @classmethod
    async def brute_community_strings(cls, ip_address: str, port: int, community_strings: set = None) -> list[dict]:
        if not community_strings:
            community_strings = {"public", "private"}
        v1 = await cls.get_community_strings_with_read_access(ip_address=ip_address, port=port, community_strings=community_strings, snmp_version=0)
        v2 = await cls.get_community_strings_with_read_access(ip_address=ip_address, port=port, community_strings=community_strings, snmp_version=1)
        result = []
        for snmp_version, community_string, error_status in v1 + v2:
            tmp = {"login" : community_string,
                   "need_auth" : bool(error_status),
                   "permissions" : 0,
                   "parameters" : json.dumps({"snmp_version": snmp_version + 1}) }
            if not error_status:
                tmp["permissions"] += 1
            if await cls.is_write_access(ip_address=ip_address, port=port, community_string=community_string, snmp_version=snmp_version):
                tmp["permissions"] += 2
            result.append(tmp)
        return result



class SnmpGet(SNMP):
    """Class for obtaining data on specific oids.

    Methods:
        system_name
        number_of_interfaces
        interface_index
        interface_description
        interface_speed
        interface_phys_address
        ip_ad_ent_addr
        ip_add_ent_if_ind
        udp_local_ports
        ip_net_to_media_if_index
        ip_net_to_media_phys_address
        ip_net_to_media_net_address
    """
    def __init__(self, ip_address: str, port: int, snmp_version: int, community_string: str, ifnumber: int):
        self.ip_address = ip_address
        self.port = port
        self.snmp_version = snmp_version
        self.community_string = community_string
        self.ifnumber = ifnumber

    @classmethod
    async def create_obj(cls, ip_address: str, port: int, snmp_version: int, community_string: str):
        """ Create SnmpGet object

        Args:
            ip_address (str): ip address
            port (int): port
            snmp_version (int): 0 - for SNMP v1; 1 - for SNMP v2c;
            community_string (str): community string

        Returns:
            _type_: _description_
        """
        ifnumber = await cls.number_of_interfaces(ip_address=ip_address, port=port, snmp_version=snmp_version, community_string=community_string)
        return cls(ip_address=ip_address, port=port, snmp_version=snmp_version, community_string=community_string, ifnumber=ifnumber)

    @classmethod
    async def number_of_interfaces(cls, ip_address: str, port: int, snmp_version: int, community_string: str) -> int:
        """ The number of network interfaces (regardless of their current state) present on this system.

        Args:
            ip_address (str): ip address
            port (int): port
            snmp_version (int):
                * 0 - for SNMP v1;
                * 1 - for SNMP v2c;
            community_string (str): community string

        Returns:
            int: ifNumber
        """
        oid = "1.3.6.1.2.1.2.1.0"               # ifNumber
        result = 0
        try:
            result = int(await cls.get_value(ip_address=ip_address, port=port, community_string=community_string, oid=oid, snmp_version=snmp_version))
        finally:
            return result


    async def system_name(self) -> str:
        """An administratively-assigned name for this managed
            node.  By convention, this is the node's fully-qualified
            domain name.  If the name is unknown, the value is
            the zero-length string.

        Args:
            ip_address (str): ip address
            port (int): port
            community_string (str): community string

        Returns:
            str: sysName
        """
        oid = "1.3.6.1.2.1.1.5.0"               # sysName
        return str(await self.get_value(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version))
    
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
        if self.ifnumber:
            for item in await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version):
                result.append(str(item))
        return result

    async def interface_description(self) -> list[str]:
        """A textual string containing information about the
            interface.  This string should include the name of the
            manufacturer, the product name and the version of the
            interface hardware/software.

        Args:
            ip_address (str): ip address
            port (int): port
            community_string (str): community string
            count (int): number of interfaces

        Returns:
            list[str]: [ifDescr]
        """
        oid = "1.3.6.1.2.1.2.2.1.2"            # ifDescr
        result = []
        if self.ifnumber:
            for item in await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version):
                result.append(str(item))
        return result

    async def interface_speed(self) -> list[int]:
        """An estimate of the interface's current bandwidth in bits
            per second. For interfaces which do not vary in bandwidth
            or for those where no accurate estimation can be made, this
            object should contain the nominal bandwidth. If the
            bandwidth of the interface is greater than the maximum value
            reportable by this object then this object should report its
            maximum value (4,294,967,295) and ifHighSpeed must be used
            to report the interace's speed. For a sub-layer which has
            no concept of bandwidth, this object should be zero.

        Returns:
            list[int]: [ifSpeed in bps]
        """
        
        oid = "1.3.6.1.2.1.2.2.1.5"     # ifSpeed [bps]
        result = []
        if self.ifnumber:
            for item in await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version):
                result.append(int(item))
        return result


    async def interface_phys_address(self) -> list[str]:
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
        oid = "1.3.6.1.2.1.2.2.1.6"     # ifPhysAddress
        result = []
        if self.ifnumber:
            for item in await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version):
                mac = ':'.join([item[2:][i:i+2].upper() for i in range(0, len(item[2:]), 2)])
                if len(mac) != 17: mac = ""
                result.append(mac)
        return result

    async def ip_ad_ent_addr(self) -> list[str]:
        """The IP address to which this entry's addressing
            information pertains. 

        Returns:
            list[str]: [ipAdEntAddr]
        """
        oid = "1.3.6.1.2.1.4.20.1.1"            # ipAdEntAddr
        result = []
        try:
            result = await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version)
        finally:
            return result
    
    async def ip_ad_ent_net_mask(self) -> list:
        """The subnet mask associated with the IPv4 address of this
            entry.

        Returns:
            list[str]: [ipAdEntNetMask]
        """

        oid = "1.3.6.1.2.1.4.20.1.3"          # ipAdEntNetMask
        result = []
        try:
            result = await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version)
        finally:
            return result


    async def ip_add_ent_if_ind(self) -> list[str]:
        """The index value which uniquely identifies the interface to
            which this entry is applicable. The interface identified by
            a particular value of this index is the same interface as
            identified by the same value of the IF-MIB's ifIndex.

        Returns:
            list: [ipAdEntIfIndex]
        """
        oid = "1.3.6.1.2.1.4.20.1.2"            # ipAdEntIfIndex
        result = []
        try:
            result = await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version)
        finally:
            return result


    async def udp_local_ports(self, ip) -> list[int]:

        oid = "1.3.6.1.2.1.7.5.1.2." + ip    # udpLocalPort
        result = []
        try:
            for item in await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version):
                result.append(int(item))
        finally:
            return result
        
    async def ip_net_to_media_if_index(self) -> list:
        """Each entry contains one IpAddress to `physical'
            address equivalence.

        Returns:
            list: [ipNetToMediaIfIndex]
        """

        oid = "1.3.6.1.2.1.4.22.1.1"        # ipNetToMediaIfIndex
        result = []
        try:
            result = await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version)
        finally:
            return result

    async def ip_net_to_media_phys_address(self) -> list:
        """The media-dependent `physical' address.

        Returns:
            list: [ipNetToMediaPhysAddress]
        """

        oid = "1.3.6.1.2.1.4.22.1.2"        # ipNetToMediaPhysAddress
        result = []
        try:
            for item in await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version):
                mac = ':'.join([item[2:][i:i+2].upper() for i in range(0, len(item[2:]), 2)])
                if len(mac) != 17: mac = ""
                result.append(mac)
        finally:
            return result
        
    async def ip_net_to_media_net_address(self) -> list:
        """The IpAddress corresponding to the media-
            dependent `physical' address.

        Returns:
            list: [ipNetToMediaNetAddress]
        """

        oid = "1.3.6.1.2.1.4.22.1.3"        # ipNetToMediaNetAddress
        result = []
        try:
            tmp = await self.get_block(ip_address=self.ip_address, port=self.port, community_string=self.community_string, oid=oid, snmp_version=self.snmp_version)
            for item in tmp:
                if all([len(str(item).split('.')) == 4] + list(map(lambda x: x.isdigit(),  str(item).split('.')))):     # TODO тут вместо IpAddrss как то пришло Counter32
                    result.append(item)
                else:
                    result.append(None)
        finally:
            return result