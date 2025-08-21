import datetime
import json

from setezor.models.certificate import Cert
from setezor.models.ip import IP
from setezor.models.port import Port
from setezor.modules.osint.cert.crt4 import CertInfo
from setezor.modules.osint.dns_info.dns_info import DNS
from setezor.restructors.dns_scan_task_restructor import DNS_Scan_Task_Restructor
from setezor.schemas.task import WebSocketMessage
from setezor.tools.websocket_manager import WS_MANAGER


class CertTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result, data: dict, **kwargs):
        try:
            cert_data = CertInfo.parse_cert(cert=raw_result)
        except Exception as e:
            message = WebSocketMessage(title="Error",
                                       text="Cert not found",
                                       type="error")
            await WS_MANAGER.send_message(entity_id=kwargs.get('project_id'), message=message)
            raise Exception("Cert not found")

        result = []
        data_for_cert_model: dict = {
            'data': json.dumps(cert_data),
            'not_before_date': datetime.datetime.fromtimestamp(cert_data['not-before']),
            'not_after_date': datetime.datetime.fromtimestamp(cert_data['not-after']),
            'is_expired': cert_data['has-expired'],
            'alt_name': cert_data.get('subjectAltName', "")
        }
        port = data.get("port")
        if ip_addr := data.get("ip"):
            ip_obj = IP(ip=ip_addr)
            result.append(ip_obj)
            port_obj = Port(port=port, ip=ip_obj)
            result.append(port_obj)
            cert_obj = Cert(ip=ip_obj, **data_for_cert_model)
            result.append(cert_obj)
        else:
            domain = data.get("domain")
            responses = [await DNS.resolve_domain(domain, "A")]
            domains = DNS.proceed_records(responses)
            domain_obj, ip_obj, *dns_obj = await DNS_Scan_Task_Restructor.restruct(domains, domain) #TODO написать проверки
            result.append(domain_obj)
            result.append(ip_obj)
            result.extend(dns_obj)
            port_obj = Port(port=port,ip=ip_obj)
            result.append(port_obj)
            cert_obj = Cert(ip=ip_obj, **data_for_cert_model)
            result.append(cert_obj)
        return result
    
    @classmethod
    def get_raw_result(cls, data):
        return data.encode()