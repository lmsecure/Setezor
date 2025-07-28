from setezor.modules.masscan.parser import BaseMasscanParser


class MasscanTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result: str, format: str, agent_id: str, interface_ip_id: str, **kwargs):
        ports = BaseMasscanParser._parser_results(format=format, input_data=raw_result)
        result_data = BaseMasscanParser.restruct_result(data=ports, agent_id=agent_id, interface_ip_id=interface_ip_id)
        return result_data
    

    @classmethod
    def get_raw_result(cls, data):
        return data.encode()