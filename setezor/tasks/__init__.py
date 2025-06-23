from setezor.restructors.cert_task_restructor import CertTaskRestructor
from setezor.restructors.dns_scan_task_restructor import DNS_Scan_Task_Restructor
from setezor.restructors.scapy_scan_task_restructor import ScapyScanTaskRestructor
from setezor.restructors.sd_find_scan_task_restructor import Sd_Scan_Task_Restructor
from setezor.restructors.snmp_scan_task_restructor import SnmpTaskRestructor
from setezor.restructors.whois_task_restructor import WhoisTaskRestructor
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
from setezor.restructors.nmap_scan_task_restructor import NmapScanTaskRestructor
from setezor.restructors.masscan_scan_task_restructor import MasscanTaskRestructor
from .speed_test_task import SpeedTestClientTask, SpeedTestServerTask
from setezor.restructors.speed_test_task_restructor import SpeedTestClientTaskRestructor, SpeedTestServerTaskRestructor

FOLDERS = {
    NmapScanTask.__name__: Folders.nmap_logs_path.value,
    MasscanScanTask.__name__: Folders.masscan_logs_path.value,
    ScapySniffTask.__name__: Folders.scapy_logs_path.value,
    CertTask.__name__: Folders.certificates_path.value,
    WhoisTask.__name__: Folders.whois_logs_path.value,
}

RESTRUCTORS = {
    NmapScanTask.__name__: NmapScanTaskRestructor,
    MasscanScanTask.__name__: MasscanTaskRestructor,
    ScapySniffTask.__name__: ScapyScanTaskRestructor,
    CertTask.__name__: CertTaskRestructor,
    WhoisTask.__name__: WhoisTaskRestructor,
    SnmpBruteCommunityStringTask.__name__: SnmpTaskRestructor,
    DNSTask.__name__: DNS_Scan_Task_Restructor,
    SdFindTask.__name__: Sd_Scan_Task_Restructor,
    SpeedTestClientTask.__name__: SpeedTestClientTaskRestructor,
    SpeedTestServerTask.__name__: SpeedTestServerTaskRestructor
}



def get_task_by_class_name(name: str):
    model_class = globals().get(name)
    
    if model_class and issubclass(model_class, BaseJob):
        return model_class
    else:
        return None
    

def get_folder_for_task(name: str):
    model_class = globals().get(name)
    if model_class and issubclass(model_class, BaseJob):
        return FOLDERS.get(model_class.__name__)
    else:
        raise ValueError(f"Модель с именем {name} не найдена или не является SQLModel.")
    
def get_restructor_for_task(name: str):
    model_class = globals().get(name)
    if model_class and issubclass(model_class, BaseJob):
        return RESTRUCTORS.get(model_class.__name__)
    else:
        raise ValueError(f"Модель с именем {name} не найдена или не является SQLModel.")