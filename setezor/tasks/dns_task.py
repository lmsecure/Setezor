from setezor.tasks.base_job import BaseJob
from setezor.models.target import Target


class DNSTask(BaseJob):

    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        for target in targets:
            if not target.domain:
                continue
            result_params.append({**base_kwargs} | {"domain" : target.domain})
            print(result_params[-1])
        return result_params