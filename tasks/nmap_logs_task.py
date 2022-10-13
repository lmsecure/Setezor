from tasks.nmap_scan_task import NmapScanTask
from modules.nmap.scanner import NmapScanner
from modules.nmap.parser import NmapParser
from tools.ip_tools import get_self_ip
from base64 import b64decode



class NmapLogTask(NmapScanTask):
    

    async def _task_func(self, log_file: str, iface: str, nmap_logs: str, *args, **kwargs):
        """Метод задачи для парсинга xml-логов nmap-а

        Args:
            xml_log (str): xml-логи

        Returns:
            _type_: результат выполнения парсинга логов
        """
        data = b64decode(log_file.split(',')[1])
        NmapScanner.save_source_data(path=nmap_logs, scan_xml=data, command='parse_xml_log')
        log_result = NmapScanner().parse_xml(input_xml=data)
        return NmapParser().parse_hosts(scan=log_result.get('nmaprun'), self_address=get_self_ip(iface))