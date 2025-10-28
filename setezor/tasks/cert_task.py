from setezor.tasks.base_job import BaseJob
from setezor.restructors.cert_task_restructor import CertTaskRestructor

class CertTask(BaseJob):
    logs_folder = "certificates"
    restructor = CertTaskRestructor
