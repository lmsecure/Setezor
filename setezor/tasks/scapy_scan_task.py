from setezor.tasks.base_job import BaseJob
from setezor.restructors.scapy_scan_task_restructor import ScapyScanTaskRestructor


class ScapySniffTask(BaseJob):
    logs_folder = "scapy_logs"
    restructor = ScapyScanTaskRestructor
