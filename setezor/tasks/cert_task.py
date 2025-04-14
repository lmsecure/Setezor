import traceback
from time import time
import json
from datetime import datetime
from setezor.tasks.base_job import BaseJob
from setezor.modules.osint.cert.crt4 import CertInfo
from setezor.tools.url_parser import parse_url
from setezor.models import IP, Port, Domain, Cert
from setezor.modules.osint.dns_info.dns_info import DNS


class CertTask(BaseJob):

    JOB_URL = "cert_info_task"

    def __init__(self, scheduler, name: str, task_id: int, target: str, port: int, agent_id: int, project_id: str):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.target = target
        self.port = port
        self.data = parse_url(f"https://{self.target}:{self.port}/")
        self.agent_id = agent_id
        self.project_id = project_id
        self._coro = self.run()

    async def _task_func(self):
        return CertInfo.get_cert_and_parse(resource=self.data)

    async def _restruct_result(self, cert_data:dict):
        result = []
        data:dict = {
            'data': json.dumps(cert_data),
            'not_before_date': datetime.fromtimestamp(cert_data['not-before']),
            'not_after_date': datetime.fromtimestamp(cert_data['not-after']),
            'is_expired': cert_data['has-expired'],
            'alt_name': cert_data.get('subjectAltName', "")
        }
        port = self.data.get("port")
        if ip_addr := self.data.get("ip"):
            ip_obj = IP(ip=ip_addr)
            result.append(ip_obj)
            port_obj = Port(port=port, ip=ip_obj)
            result.append(port_obj)
            cert_obj = Cert(ip=ip_obj, **data)
            result.append(cert_obj)
        else:
            domain = self.data.get("domain")
            responses = [await DNS.resolve_domain(domain, "A")]
            domain_obj, ip_obj, dns_obj = DNS.proceed_records(domain, responses)
            result.append(domain_obj)
            result.append(ip_obj)
            result.append(dns_obj)
            port_obj = Port(port=port,ip=ip_obj)
            result.append(port_obj)
            cert_obj = Cert(ip=ip_obj, **data)
            result.append(cert_obj)
        return result
        
    @BaseJob.remote_task_notifier
    async def run(self):
        cert_data, raw_result = await self._task_func()
        result = await self._restruct_result(cert_data=cert_data)
        return result, raw_result.encode(), "pem"