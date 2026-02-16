import socket

from setezor.db.entities import DNSTypes
from setezor.models import DNS, Domain, IP, Port
from setezor.modules.site_parser.screenshoter import ScreenshotModule
from setezor.modules.site_parser.wappalyzer import WappalyzerModule
from setezor.modules.site_parser.web_archive import WebArchiveModule
from setezor.modules.wappalyzer.wappalyzer import WappalyzerParser
from setezor.tools.url_parser import parse_url
from setezor.tools.zip_files_manager import Base64


class ParseSiteTaskRestructor:

    @classmethod
    def _resolve_ip(cls, domain: str) -> str: # FixMe change to DNSModule.resolve_domain(domain, "A")
        """Резолвит IP адрес домена"""
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror:
            return "0.0.0.0"

    @classmethod
    async def restruct(cls, url: str, har: Base64, screenshot: Base64, wappalyzer_data: list[dict], **kwargs):
        url_data = parse_url(url)
        if url_data.get('domain', None) is not None and url_data.get('ip', None) is None:
            domain = url_data.get('domain')
            ip = cls._resolve_ip(domain)
        elif url_data.get('ip', None) is not None and url_data.get('domain', None) is None:
            ip = url_data.get('ip')
            domain = ''

        entities = []
        domain_obj = Domain(domain=domain)
        ip_obj = IP(ip=ip)
        dns_obj = DNS(target_domain=domain_obj, dns_type_id=DNSTypes.A.value, target_ip=ip_obj)
        port_obj = Port(ip=ip_obj, port=url_data['port'], state='open', protocol='tcp', service_name='http')
        entities += [domain_obj, ip_obj, dns_obj, port_obj]
        web_archive_parsed_data = await WebArchiveModule.parse(har, **kwargs)
        entities += await WebArchiveModule.restruct_result(url, dns_obj=dns_obj, name=web_archive_parsed_data['name'])
        if screenshot:
            screenshot_parsed_data = await ScreenshotModule.parse(screenshot, **kwargs)
            screenshot_entities = await ScreenshotModule.restruct_result(screenshot_parsed_data['screenshot_id'], dns_obj=dns_obj)
            entities += screenshot_entities
        if wappalyzer_data:
            wappalyzer_data = WappalyzerModule.prepare_wappalyzer_data(wappalyzer_data, url)
            WappalyzerModule.save(wappalyzer_data, **kwargs)
            wappalyzer_parsed_data = WappalyzerParser.parse_json(
                wappalyzer_data, groups=WappalyzerParser.groups.keys()
            )
            wappalyzer_entities = await WappalyzerParser.restruct_result(
                wappalyzer_parsed_data, domain_obj=domain_obj, dns_obj=dns_obj, port_obj=port_obj
            )
            entities += wappalyzer_entities

        return entities