from setezor.tasks.base_job import BaseJob
from setezor.models.target import Target
from setezor.restructors.dns_scan_task_restructor import DNS_Scan_Task_Restructor


class DNSTask(BaseJob):
    restructor = DNS_Scan_Task_Restructor


    @classmethod
    def clean_payload(cls, version: str, payload: dict):
        if list(map(int, version.split('.'))) > [1, 0, 4]:
            return
        payload.pop("records", None)
        payload.pop("ns_servers", None)


    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        for target in targets:
            if not target.domain:
                continue
            result_params.append({**base_kwargs} | {"domain" : target.domain})
        return result_params