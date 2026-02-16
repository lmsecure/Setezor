from .base_job import BaseJob
from setezor.models.target import Target
from setezor.restructors.rdap_task_restructor import RdapTaskRestructor

class RdapTask(BaseJob):
    logs_folder = "rdap_logs"
    restructor = RdapTaskRestructor

    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        for target in targets:
            if target.domain:
                result_params.append({**base_kwargs} | {"target" : target.domain})
        return result_params