from setezor.tasks.base_job import BaseJob
from setezor.restructors.cert_task_restructor import CertTaskRestructor
from setezor.models.target import Target

class CertTask(BaseJob):
    logs_folder = "certificates"
    restructor = CertTaskRestructor

    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        params = []
        for t in targets:
            addresses = []
            if t.ip:
                addresses.append(t.ip.split('/')[0].strip())
            if t.domain:
                addresses.append(t.domain.strip())
            
            for addr in addresses:
                port = int(t.port) if t.port else 443
                
                params.append({
                    **base_kwargs,
                    "target": addr,
                    "port": port
                })
        return params