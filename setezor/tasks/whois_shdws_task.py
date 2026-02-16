from .base_job import BaseJob
from setezor.models.target import Target
from setezor.restructors.whois_shdws_task_restructor import WhoisShdwsTaskRestructor

class WhoisShdwsTask(BaseJob):
    restructor = WhoisShdwsTaskRestructor
    logs_folder = "whois_shdws_logs_path"



    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        for target in targets:
            if target.ip:
                result_params.append({**base_kwargs} | {"target" : target.ip.partition('/')[0]})
        return result_params
