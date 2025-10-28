import json
from base64 import b64decode
from setezor.tasks.base_job import BaseJob
from setezor.modules.wappalyzer.wappalyzer import WappalyzerParser



class WappalyzerLogsTask(BaseJob):
    logs_folder = "wappalyzer_logs"

    def __init__(self, task_manager,
                 scheduler,
                 name: str,
                 task_id: str,
                 project_id: str,
                 scan_id: str,
                 agent_id: str,
                 groups: list[str],
                 file: str,
                 filename: str):
        super().__init__(scheduler=scheduler, name=name)
        self.task_manager = task_manager
        self.task_id = task_id
        self.project_id = project_id
        self.scan_id = scan_id
        self.agent_id = agent_id
        self.file = file
        self.filename = filename
        self.groups = groups
        self._coro = self.run()


    async def _task_func(self):
        data = b64decode(self.file.split(',')[1])
        json_file = json.loads(data.decode())
        return WappalyzerParser.parse_json(wappalyzer_log=json_file, groups=self.groups)

    @BaseJob.local_task_notifier
    async def run(self):
        data = await self._task_func()
        return await WappalyzerParser.restruct_result(data=data)