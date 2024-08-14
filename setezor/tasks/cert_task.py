import traceback
import asyncio
from time import time
from datetime import datetime
import socket
from typing import Any, Dict
from setezor.tools import ip_tools

from .base_job import BaseJob, MessageObserver
from setezor.modules.osint.cert.crt4 import CertInfo
from setezor.database.queries import Queries


class CertInfoTask(BaseJob):
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int,
                 port: str, target: str, certificates_folder: str, db: Queries):
        super().__init__(observer = observer, scheduler = scheduler, name = name)
        self.target = target
        self.port = port
        self._coro = self.run(db=db, task_id=task_id, port=port,
                              target=target, certificates_folder=certificates_folder)

    def is_ip_address(address):
        try:
            socket.inet_aton(address)
            return True
        except OSError:
            return False

    async def _task_func(self, target: str, port: str, certificates_folder: str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, CertInfo.get_cert_and_parse, target, port, certificates_folder)

    def _write_result_to_db(self, db: Queries, result):
        data:Dict[str,Any] = dict()
        if ip_tools.is_ip_address(self.target):
            data.update({'ip': self.target})
        else:
            data.update({'domain': self.target})
        data.update({
            'port': self.port,
            'data': result,
            'not_before_date': datetime.fromtimestamp(result['not-before']),
            'not_after_date': datetime.fromtimestamp(result['not-after']),
            'is_expired': result['has-expired'],
            'alt_name': result.get('subjectAltName', "")
        })
        db.Cert.get_or_create(**data)

    async def run(self, db: Queries, task_id: int, target: str, port: str, certificates_folder: str):
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
            result = await self._task_func(target=target, port=port, certificates_folder=certificates_folder)

            self.logger.debug('Task func "%s" finished after %.2f seconds',
                              self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, result=result)
            self.logger.debug('Result of task "%s" wrote to db',
                              self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s',
                              self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(
                index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)
