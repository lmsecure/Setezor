from tasks.base_task import BaseTask
from modules.screenshoter.screenshoter import Screenshoter
from database.queries import Queries

class ScreenshotTask(BaseTask):
    
    task_type = 'sceenshot'
    
    @staticmethod
    def _task_func(ip: str, port: int, file_path: str, file_name: str, with_params: bool):
        screenshoter = Screenshoter()
        result = screenshoter.take_screenshot_by_ip_port(ip=ip, port=port, file_path=file_path, file_name=file_name, with_params=with_params)
        return result
    
    def _write_result_to_db(self, db: Queries, task_id: int, params: dict, *args, **kwargs):
        db.screenshot.create_screenshot(task_id=task_id, **params)