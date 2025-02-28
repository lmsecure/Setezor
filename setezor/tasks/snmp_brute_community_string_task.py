from setezor.tasks.base_job import BaseJob
from setezor.modules.snmp.snmp import SnmpGettingAccess
from setezor.modules.snmp.parser import SnmpParser



class SnmpBruteCommunityStringTask(BaseJob):
    def __init__(self, scheduler, name: str, task_id: int, project_id: str, agent_id: str,
            target_ip: str, target_port: int, community_strings_file: str):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.project_id = project_id
        self.agent_id = agent_id
        self.target_ip = target_ip
        self.target_port = target_port
        self.community_strings = SnmpParser.parse_community_strings_file(file = community_strings_file)
        self._coro = self.run()

    async def _task_funk(self):
        return await SnmpGettingAccess.brute_community_strings(ip_address=self.target_ip, port=self.target_port, community_strings=self.community_strings)

    @BaseJob.remote_task_notifier
    async def run(self):
        data = await self._task_funk()
        result = SnmpParser.restruct_result(ip=self.target_ip, port=self.target_port, data=data)
        return result, b"", ""
