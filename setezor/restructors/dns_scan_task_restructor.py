import json

from setezor.modules.dns_lookup.parser import DNS_LookupParse


class DNS_Scan_Task_Restructor:
    @classmethod
    async def restruct(cls, project_id: str, scan_id: str, agent_id: str, raw_result: list[dict], domain_name: str, **kwargs) -> list:
        result = await DNS_LookupParse.restruct_result(project_id=project_id, scan_id=scan_id, agent_id=agent_id,
                                                       raw_result=raw_result, domain_name=domain_name)
        return result


    @classmethod
    def get_raw_result(cls, data):
        return json.dumps(data).encode()
