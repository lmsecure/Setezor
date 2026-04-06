import orjson

from setezor.modules.osint.whois_shdws.whois_shdws_parser import WhoisShdwsParser



class WhoisShdwsTaskRestructor:

    @classmethod
    async def restruct(cls, project_id: str, scan_id: str, raw_result, target: str, **kwargs) -> list:
        parse_data = WhoisShdwsParser.parse(raw_data=raw_result, target=target)
        result = WhoisShdwsParser.restructor(data=parse_data)
        return result



    @classmethod
    def get_raw_result(cls, data):
        return orjson.dumps(data)
