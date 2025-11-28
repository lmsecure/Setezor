from .base_job import BaseJob
from setezor.models.target import Target
from setezor.restructors.whois_task_restructor import WhoisTaskRestructor

class WhoisTask(BaseJob):
    restructor = WhoisTaskRestructor
    logs_folder = "whois_logs_path"



    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        for target in targets:
            if target.ip:
                result_params.append({**base_kwargs} | {"target" : target.ip.partition('/')[0]})
            if target.domain:
                result_params.append({**base_kwargs} | {"target" : target.domain})
        return result_params
