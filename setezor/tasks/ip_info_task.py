from .base_job import BaseJob
from setezor.models.target import Target
from setezor.restructors.ip_info_restructor import IpInfoRestructor



class IpInfoTask(BaseJob):
    restructor = IpInfoRestructor


    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        for target in targets:
            if not target.ip:
                continue
            result_params.append({**base_kwargs} | {"target" : target.ip.partition('/')[0]})
        return result_params
