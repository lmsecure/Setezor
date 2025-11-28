from setezor.modules.ip_info.parser import IpInfoParser



class IpInfoRestructor:

    @classmethod
    async def restruct(cls, target: str, raw_result, agent_id: str, **kwargs):
        return IpInfoParser.restruct_result(target = target, data=raw_result)
