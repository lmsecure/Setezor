from setezor.tasks.base_job import BaseJob
from .dns_task import DNSTask
from .nmap_parse_task import NmapParseTask
from .cert_task import CertTask
from .domain_task import SdFindTask
from .whois_task import WhoisTask
from .nmap_scan_task import NmapScanTask
from .scapy_scan_task import ScapySniffTask
from .masscan_scan_task import MasscanScanTask
from .snmp_brute_community_string_task import SnmpBruteCommunityStringTask
from setezor.managers.project_manager.structure import Folders


FOLDERS = {
    NmapScanTask.__name__: Folders.nmap_logs_path.value,
    MasscanScanTask.__name__: Folders.masscan_logs_path.value,
    ScapySniffTask.__name__: Folders.scapy_logs_path.value,
    CertTask.__name__: Folders.certificates_path.value,
    WhoisTask.__name__: Folders.whois_logs_path.value,
    SnmpBruteCommunityStringTask.__name__: Folders.whois_logs_path.value,
}


def get_task_by_class_name(name: str):
    model_class = globals().get(name)
    
    if model_class and issubclass(model_class, BaseJob):
        return model_class
    else:
        raise ValueError(f"Модель с именем {name} не найдена или не является SQLModel.")
    

def get_folder_for_task(name: str):
    model_class = globals().get(name)
    if model_class and issubclass(model_class, BaseJob):
        return FOLDERS.get(model_class.__name__)
    else:
        raise ValueError(f"Модель с именем {name} не найдена или не является SQLModel.")