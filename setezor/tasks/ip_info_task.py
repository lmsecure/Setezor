from .base_job import BaseJob
from setezor.models.target import Target
from setezor.restructors.ip_info_restructor import IpInfoRestructor



class IpInfoTask(BaseJob):
    restructor = IpInfoRestructor


    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        seen = set()
        for target in targets:
            if not target.ip:
                continue
            ip = target.ip.partition('/')[0]
            if ip not in seen:
                seen.add(ip)
                result_params.append({**base_kwargs} | {"target" : ip})
        return result_params
