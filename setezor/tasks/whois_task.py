from .base_job import BaseJob
from setezor.restructors.whois_task_restructor import WhoisTaskRestructor

class WhoisTask(BaseJob):
    restructor = WhoisTaskRestructor
    logs_folder = "whois_logs_path"
