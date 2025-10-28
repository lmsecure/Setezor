from setezor.tasks.base_job import BaseJob
from setezor.restructors.snmp_scan_task_restructor import SnmpTaskRestructor

class SnmpBruteCommunityStringTask(BaseJob):
    restructor = SnmpTaskRestructor
