import json
import ssl
import OpenSSL.crypto
from datetime import datetime

from setezor.models import Cert, IP, Port, Network
from setezor.modules.osint.dns_info.dns_info import DNS
from setezor.restructors.dns_scan_task_restructor import DNS_Scan_Task_Restructor

from setezor.tools.ip_tools import get_network



class CertInfo:

    @classmethod
    def convert_timestamp(cls, cert_date: bytes):
        datetime_obj = datetime.strptime(cert_date.decode(), '%Y%m%d%H%M%SZ')
        return int(datetime.timestamp(datetime_obj))

    @classmethod
    def get_cert(cls, host: str, port: int) -> str:
        # try:
            #logger.debug('Try get cert from  %s:%s ', (host, port))
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_OPTIONAL
            cert = ssl.get_server_certificate((host, port), timeout=1)
            return cert
        # except Exception as e:
            #logger.error(f'[-] HOST: {host}, PORT: {port} {type(e).__name__}')
            # return None

    @classmethod
    def parse_cert(cls, cert: bytes) -> dict[str, str]:
        cert: OpenSSL.crypto.X509 = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, cert)
        cert_data = {
            "subject": ', '.join(['='.join([j.decode() for j in i]) for i in cert.get_subject().get_components()]),
            "issuer": ', '.join(['='.join([j.decode() for j in i]) for i in cert.get_issuer().get_components()]),
            "has-expired": cert.has_expired(),
            "not-after": cls.convert_timestamp(cert.get_notAfter()),
            "not-before": cls.convert_timestamp(cert.get_notBefore()),
            "serial-number": cert.get_serial_number(),
            "serial-number(hex)": hex(cert.get_serial_number()),
            "signature-algorithm": cert.get_signature_algorithm().decode(),
            "version": cert.get_version(),
            "pulic-key-length": cert.get_pubkey().bits()
        }

        for i in range(cert.get_extension_count()):
            inf = cert.get_extension(i)
            try:
                cert_data[inf.get_short_name().decode()] = inf.__str__()
            except:
                 continue

        return cert_data

    @classmethod
    def get_cert_and_parse(cls, resource: dict):
        port = resource.get("port")
        host = resource.get("domain") if resource.get("domain") else resource.get("ip")
        cert = cls.get_cert(host=host, port=port)
        if not cert:
            return []
        return cert

    @classmethod
    async def restruct(cls, project_id: str, scan_id: str, agent_id: str,
                 data: dict, cert_data: dict):
        result = []
        data_for_cert_model: dict = {
            'data': json.dumps(cert_data),
            'not_before_date': datetime.fromtimestamp(float(cert_data['not-before'])),
            'not_after_date': datetime.fromtimestamp(float(cert_data['not-after'])),
            'is_expired': cert_data['has-expired'],
            'alt_name': cert_data.get('subjectAltName', "")
        }
        port = data.get("port")
        if ip_addr := data.get("ip"):
            start_ip, broadcast = get_network(ip=ip_addr, mask=24)
            network_obj = Network(start_ip=start_ip, mask=24)
            ip_obj = IP(ip=ip_addr, network=network_obj)
            result.append(ip_obj)
            port_obj = Port(port=port, ip=ip_obj)
            result.append(port_obj)
            cert_obj = Cert(ip=ip_obj, **data_for_cert_model)
            result.append(cert_obj)
        else:
            domain = data.get("domain")
            responses = [await DNS.resolve_domain(domain, "A")]
            domains = DNS.proceed_records(responses)
            domain_obj, network_obj, ip_obj, *dns_obj = await DNS_Scan_Task_Restructor.restruct(project_id=project_id, scan_id=scan_id, agent_id=agent_id, raw_result=domains, domain_name=domain) #TODO написать проверки
            result.append(domain_obj)
            result.append(network_obj)
            result.append(ip_obj)
            result.extend(dns_obj)
            port_obj = Port(port=port,ip=ip_obj)
            result.append(port_obj)
            cert_obj = Cert(ip=ip_obj, **data_for_cert_model)
            result.append(cert_obj)
        return result