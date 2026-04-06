from setezor.modules.osint.rdap.rdap_parser import RdapParser
import orjson



class RdapTaskRestructor:

    @classmethod
    async def restruct(cls, raw_result, target: str, project_id: str, scan_id: str, **kwargs):
        if not raw_result:
            return []
        result = RdapParser.parse(raw_data=raw_result, target=target)
        return RdapParser.restructor(data=result, target=target)


    @classmethod
    def get_raw_result(cls, data):
        return orjson.dumps(data)