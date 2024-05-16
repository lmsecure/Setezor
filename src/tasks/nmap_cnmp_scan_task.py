
from ..app_routes.custom_types import MessageObserver
from ..modules.snmp import NmanSnmpParser
from .base_job import BaseJob, SubprocessJob, SubprocessResult
from ..database.queries import Queries

class NmapCnmpScanTask(BaseJob):
    
    parser = NmanSnmpParser()
    
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, scanning_ip: str, masscan_log_path: str, db: Queries, port: str = '161'):
        super().__init__(observer, scheduler, name)
        self._coro = self.run(db=db, task_id=task_id, port=port, scanning_ip=scanning_ip, masscan_log_path=masscan_log_path)
    
    async def run(self, db: Queries, task_id: int, scanning_ip: str, masscan_log_path: str, port: str = '161'):
        
        command = ['nmap', '--privileged', '-oX', masscan_log_path, '-sU', '-p', port, scanning_ip, '-sC']
        job = SubprocessJob(command)
        res = await job()
        return res