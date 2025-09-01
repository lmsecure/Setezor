import base64
import socket
from uuid import uuid4

from setezor.models import DNS_A, IP, DNS_A_Screenshot, Domain, Screenshot
from setezor.tools.screenshot import save_screenshot_file
from urllib.parse import urlparse



class DNSAScreenshotProcessedData:

    @classmethod
    def _resolve_ip(cls, domain: str) -> str:
        """Резолвит IP адрес домена"""
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror:
            return "0.0.0.0"

    @classmethod
    def from_restructor_data(cls, raw_result: str, url: str) -> dict:
        screenshot_bytes = base64.b64decode(raw_result)
        domain = urlparse(url).netloc
        ip = cls._resolve_ip(domain)
        import hashlib
        filename = f"{uuid4().hex}.png"
        return {
            "url": url,
            "domain": domain,
            "ip": ip,
            "screenshot_bytes": screenshot_bytes,
            "filename": filename
        }



class DNSAScreenshotTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result: str, agent_id: str, **kwargs):
        project_id = kwargs.get("project_id", "default")
        scan_id = kwargs.get("scan_id", "default")
        url = kwargs["url"]

        processed_data = DNSAScreenshotProcessedData.from_restructor_data(
            raw_result=raw_result, url=url
        )

        file_path = save_screenshot_file(
            project_id, processed_data.get("screenshot_bytes"), processed_data.get("filename"), scan_id
        )

        screenshot = Screenshot(path=file_path)
        domain = Domain(domain=processed_data.get("domain"))
        ip_obj = IP(ip=processed_data.get("ip"))
        dns_a = DNS_A(target_ip=ip_obj, target_domain=domain)
        dns_a_screenshot = DNS_A_Screenshot(dns_a=dns_a, screenshot=screenshot)

        return [screenshot, domain, ip_obj, dns_a, dns_a_screenshot]

    @classmethod
    def get_raw_result(cls, data: str) -> bytes:
        """Декодирует base64 скриншот в bytes"""
        return base64.b64decode(data)
