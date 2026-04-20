from .base_job import BaseJob
from setezor.models.target import Target
from setezor.restructors.whois_shdws_task_restructor import WhoisShdwsTaskRestructor

class WhoisShdwsTask(BaseJob):
    restructor = WhoisShdwsTaskRestructor
    logs_folder = "whois_shdws_logs_path"



    @classmethod
    async def generate_params_from_scope(cls, targets: list[Target], project_id: str, **base_kwargs):
        result_params = []
        seen = set()
        for target in targets:
            if target.ip:
                ip = target.ip.partition('/')[0].strip()
                if ip not in seen:
                    seen.add(ip)
                    result_params.append({**base_kwargs} | {"target": ip})
        return result_params
