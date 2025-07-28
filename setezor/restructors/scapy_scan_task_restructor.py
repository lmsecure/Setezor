from setezor.modules.sniffing.scapy_parser import ScapyParser
import base64

class ScapyScanTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result: str, agent_id: str, **kwargs):
        b64decoded_logs = base64.b64decode(raw_result)
        result = ScapyParser.parse_logs(data=b64decoded_logs)
        result = await ScapyParser.restruct_result(data=result, agent_id=agent_id)
        return result
    

    @classmethod
    def get_raw_result(cls, data):
        b64decoded_logs = base64.b64decode(data)
        return b64decoded_logs