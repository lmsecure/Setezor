from setezor.modules.osint.rdap.rdap_parser import RdapParser
import json
import orjson

class RdapTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result, target: str, **kwargs):
        if not raw_result:
            return []
        result = RdapParser.parse(raw_result)
        return RdapParser.restructor(data=result, target=target)
    
        
    @classmethod
    def get_raw_result(cls, data):
        return orjson.dumps(data)