from abc import ABC, abstractmethod
from database.queries import Queries
import traceback
from time import time
from exceptions.loggers import get_logger, LoggerNames


class BaseTask(ABC):
    """Базовый  класс для задач
    """
    
    def __init__(self):
        self.logger = get_logger(logger_name=LoggerNames.task)
    
    async def _task_func(self, *args, **kwargs):
        pass
    
    def _write_result_to_db(self, *args, **kwargs):
        pass
    
    async def execute(self, db: Queries, task_id: int, *args, **kwargs):
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
            result = await self._task_func(*args, **kwargs)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, result=result, **kwargs)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            return
        db.task.set_finished_status(index=task_id)