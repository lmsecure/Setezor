import traceback
from setezor.modules.screenshoter.screenshoter import Screenshoter
from setezor.database.queries import Queries
from .base_job import BaseJob, MessageObserver
from time import time


class ScreenshotTask(BaseJob):
    def __init__(self, observer: MessageObserver, scheduler, name: str,
                 task_id: int, db: Queries, url: str, screenshots_folder: str, timeout: float, **kwargs):
        super().__init__(observer=observer, scheduler=scheduler, name=name)
        self._coro = self.run(db=db, task_id=task_id, url=url,
                              screenshots_folder=screenshots_folder, timeout=timeout, **kwargs)

    async def _task_func(self, url: str, screenshots_folder: str, timeout: float):
        pathes = await Screenshoter.take_screenshot(
            url=url, screenshots_folder=screenshots_folder,timeout=timeout)
        return pathes

    def _write_result_to_db(self, db: Queries, result: list[str], url: str, **kwargs):
        resource = db.resource.get_or_create(**kwargs)
        db.screenshot.get_or_create(resource_id=resource.id, path=result)

    async def run(self, db: Queries, task_id: int, url: str, screenshots_folder: str, timeout: float, **kwargs):
        """Метод выполнения задачи
        1. Произвести операции согласно методу self._task_func
        2. Записать результаты в базу согласно методу self._write_result_to_db
        3. Попутно менять статут задачи

        Args:
            db (Queries): объект запросов к базе
            task_id (int): идентификатор задачи
        """
        db.task.set_pending_status(index=task_id)
        try:
            t1 = time()
            result = await self._task_func(url=url, screenshots_folder=screenshots_folder, timeout=timeout)
            self.logger.debug('Task func "%s" finished after %.2f seconds',
                              self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, result=result, url=url, **kwargs)
            self.logger.debug('Result of task "%s" wrote to db',
                              self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s',
                              self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(
                index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)
