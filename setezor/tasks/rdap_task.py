from .base_job import BaseJob
from setezor.models.target import Target
from setezor.restructors.rdap_task_restructor import RdapTaskRestructor

class RdapTask(BaseJob):
    logs_folder = "rdap_logs"
    restructor = RdapTaskRestructor

    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        seen = set()
        for target in targets:
            if target.domain:
                domain = target.domain.strip()
                if domain not in seen:
                    seen.add(domain)
                    result_params.append({**base_kwargs} | {"target": domain})
        return result_params