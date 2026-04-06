from setezor.tasks.base_job import BaseJob
from setezor.models.target import Target
from setezor.restructors.dns_scan_task_restructor import DNS_Scan_Task_Restructor


class DNSTask(BaseJob):
    restructor = DNS_Scan_Task_Restructor
    logs_folder = 'lookup_logs'


    @classmethod
    def clean_payload(cls, version: str, payload: dict):
        if list(map(int, version.split('.'))) > [1, 0, 4]:
            return
        payload.pop("records", None)
        payload.pop("ns_servers", None)


    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        seen = set()
        for target in targets:
            if not target.domain:
                continue
            domain = target.domain.strip()
            if domain not in seen:
                seen.add(domain)
                result_params.append({**base_kwargs} | {"domain": domain})
        return result_params