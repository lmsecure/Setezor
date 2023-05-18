from modules.screenshoter.screenshoter import Screenshoter
from database.queries import Queries

class ScreenshotFromIPTask:
    
    @staticmethod
    async def _task_func(phantomjs_path: str, script_path: str, ip: str, port: int, file_path: str, file_name: str, schema: str = None, *args, **kwargs):
        screenshoter = Screenshoter(phantom_path=phantomjs_path, script_path=script_path)
        pathes = await screenshoter.take_screenshot(ip=ip, port=port, folderpath=file_path, filename=file_name, schema=schema)
        return {'ip': ip, 'port': port, 'pathes': pathes}
    
    def _write_result_to_db(self, db: Queries, task_id: int, result: dict, *args, **kwargs):
        ip, port, pathes = result.values()
        for screenshot_path in pathes:
            db.screenshot.create(path=screenshot_path, task_id=task_id, ip=ip, port=port)