import traceback
from time import time
import json
from datetime import datetime
from setezor.tasks.base_job import BaseJob
from setezor.modules.osint.cert.crt4 import CertInfo
from setezor.tools.url_parser import parse_url
from setezor.models import IP, Port, Domain, L7, Cert
from setezor.modules.osint.dns_info.dns_info import DNS


class CertTask(BaseJob):

    JOB_URL = "cert_info_task"

    def __init__(self, scheduler, name: str, task_id: int, target: str, port: int, agent_id: int, project_id: str):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.target = target
        self.port = port
        self.data = parse_url(f"{self.target}:{self.port}")
        self.agent_id = agent_id
        self.project_id = project_id
        self._coro = self.run()

    async def _task_func(self):
        return CertInfo.get_cert_and_parse(resource=self.data)

    async def _write_result_to_db(self, cert_data:dict):
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
            l7_obj = L7(port=port_obj)
            result.append(l7_obj)
            cert_obj = Cert(l7 = l7_obj, **data)
            result.append(cert_obj)
        else:
            domain = self.data.get("domain")
            domain_obj = Domain(domain=domain)
            result.append(domain_obj)
            responses = [await DNS.resolve_domain(domain, "A")]
            dns_records = DNS.proceed_records(domain, responses)
            ip_obj = None
            for obj in dns_records:
                if isinstance(obj, IP):
                    ip_obj = IP(ip=obj.ip)
                    result.append(ip_obj)
            port_obj = Port(port=port,ip=ip_obj)
            result.append(port_obj)
            l7_obj = L7(port=port_obj, domain=domain_obj)
            result.append(l7_obj)
            cert_obj = Cert(l7 = l7_obj, **data)
            result.append(cert_obj)
        await self.send_result_to_parent_agent(result=result)

    async def run(self):
        """Метод выполнения задачи
        1. Произвести операции согласно методу self._task_func
        2. Записать результаты в базу согласно методу self._write_result_to_db
        3. Попутно менять статут задачи

        Args:
            db (Queries): объект запросов к базе
            task_id (int): идентификатор задачи
        """
        try:
            t1 = time()
            result = await self._task_func()
            await self._write_result_to_db(cert_data=result)
        except Exception as e:
            print('Task "%s" failed with error\n%s',
                  self.__class__.__name__, traceback.format_exc())
            raise e