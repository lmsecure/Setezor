import orjson
from setezor.modules.sd_find.sd_find import SdScanParser


class Sd_Scan_Task_Restructor:
    @classmethod
    async def restruct(cls, raw_result, **kwargs):
        if not raw_result:
            return []
        parsed = SdScanParser.parse(raw_result)
        return SdScanParser.restructor(parsed)

    @classmethod
    def get_raw_result(cls, data):
        return orjson.dumps(data)