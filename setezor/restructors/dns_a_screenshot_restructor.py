import base64

from setezor.models import DNS_A, IP, DNS_A_Screenshot, Domain, Screenshot
from setezor.schemas.dns_a_screenshot import DNSAScreenshotProcessedData
from setezor.tools.screenshot import save_screenshot_file


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
            project_id, processed_data.screenshot_bytes, processed_data.filename, scan_id
        )

        screenshot = Screenshot(path=file_path)
        domain = Domain(domain=processed_data.domain)
        ip_obj = IP(ip=processed_data.ip)
        dns_a = DNS_A(target_ip=ip_obj, target_domain=domain)
        dns_a_screenshot = DNS_A_Screenshot(dns_a=dns_a, screenshot=screenshot)

        return [screenshot, domain, ip_obj, dns_a, dns_a_screenshot]

    @classmethod
    def get_raw_result(cls, data: str) -> bytes:
        """Декодирует base64 скриншот в bytes"""
        return base64.b64decode(data)
