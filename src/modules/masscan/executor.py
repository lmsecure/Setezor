import traceback
import re
from datetime import datetime
from exceptions.loggers import get_logger
from time import time
from dataclasses import dataclass
from typing import List, Type
from logging import Logger
import aiofiles
from subprocess import Popen, PIPE
import re
from asyncio import create_subprocess_shell as async_shell
from asyncio.subprocess import PIPE as asyncPIPE

class SubrocessError(Exception):
    
    def __init__(self, result: str, error: str, code: int) -> None:
        self.result = result
        self.error = error
        self.code = code
        result = f'\nResult:\n{result}' if result else ''
        error = f'\nError:\n{error}' if error else ''
        message = f"""Subrocess task is failed with status code {code}{result}{error}"""
        super().__init__(message)

def create_shell_subprocess(command: list):
    return Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf8', errors='backslashreplace')

async def create_async_shell_subprocess(command: list):
    return await async_shell(' '.join(command), stdin=asyncPIPE, stdout=asyncPIPE, 
                             stderr=asyncPIPE)


def check_superuser_previliges(password: str):
    res, err = create_shell_subprocess('timeout 0.1 sudo -S -v'.split()).communicate(password)
    if re.match(r'^\[sudo\] password for [^\n]+?$', err) or not err:
        return True
    else:
        return False


@dataclass
class ConsoleArgument:
    argument: str
    value: str
    default_value: str
    is_flag: bool
    delimiter: str
    is_required: bool
    only_value: bool
    
    def __init__(self, argument: str, value: str, default_value: str=None, is_flag: bool=False, delimiter: str=" ",
                 is_required: bool=False, only_value: bool=False):
        # FixMe is_flag and only_value dont be used together
        self.argument = argument
        self.value = value
        self.default_value = default_value
        self.is_flag = is_flag
        self.delimiter = delimiter
        self.is_required = is_required  # FixMe unused
        self.only_value = only_value
      
    def __str__(self):
        if  self.value is None and self.default_value is None and not self.is_flag:
            raise Exception(f'Argument "{self.argument}" have no value or default value and there is not flag')
        value = self.value if not self.value is None else self.default_value
        if self.is_flag:
            if value is True:
                return self.argument
            else: 
                return ''
        elif self.only_value:
            return value
        else:
            return f'{self.argument}{self.delimiter}{value}'


class ListConsoleArgument:
    def __init__(self,):
        self.list_args: List[Type[ConsoleArgument]] = []
    
    def append(self, console_arg: ConsoleArgument, update_policy: str='nothing'):
        if not self.exists(console_arg):
            self.list_args.append(console_arg)
        else:
            if update_policy == 'replace':
                self.update(console_arg)
            else:
                return False
        
    def exists(self, arg: ConsoleArgument) -> List[Type[ConsoleArgument]]:
        return [i for i in self.list_args if arg.argument == i.argument]
    
    def clear_empty_args(self,) -> None:
        to_delete = []
        for i in self.list_args:
            if i.value is None and i.default_value is None and not i.is_flag:
                to_delete.append(i)
            if i.value is None and i.default_value is None and i.only_value:
                to_delete.append(i)
        for i in to_delete:
            self.list_args.remove(i)
    
    def prepare_command(self, command: str) -> List[Type[str]]:
        return f'{command } {" ".join([str(i) for i in self.list_args])}'.split()
    
    def update(self, console_arg: ConsoleArgument) -> None:
        exists = self.exists(console_arg)
        if exists:
            self.list_args[self.list_args.index(exists[0])] = console_arg


class ConsoleCommandExecutor:
    arguments: ListConsoleArgument
    command: str
    logger: Logger
    
    
    def __init__(self) -> None:
        self.arguments = ListConsoleArgument()
    
    def prepare_command(self):
        if len(self.arguments):
            pass
        else:
            raise Exception(f'Command "{self.command}" have no arguments')
    
    def sync_execute(self, extension: str='log'):
        self.arguments.clear_empty_args()
        execution_command = self.arguments.prepare_command(self.command)
        start_time = time()
        process = create_shell_subprocess(execution_command)
        result, error = process.communicate()
        code = process.returncode
        # ToDo add save source data
        self.logger.debug('Finish async "%s" execution after %.2f seconds', self.command, time() - start_time)
        return result, error, code
    
    async def async_execute(self, log_path: str=None, extension: str='log'):
        self.arguments.clear_empty_args()
        execution_command = self.arguments.prepare_command(self.command)
        start_time = time()
        process = await create_async_shell_subprocess(execution_command)
        result, error = await process.communicate()
        result = result.decode(encoding='utf8', errors='backslashreplace')
        error = error.decode(encoding='utf8', errors='backslashreplace')
        code= process.returncode
        if log_path:
            await self.__class__.save_source_data(path=log_path, source_data=result, command='masscan', extension=extension)
        self.logger.debug('Finish async "%s" execution after %.2f seconds', self.command, time() - start_time)
        return result, error, code
    
    @classmethod
    async def save_source_data(cls, path: str, source_data: str | bytes, command: str, extension: str='log') -> bool:
        """Метод сохранения сырых логов инструмента

        Args:
            path (str): путь до папки сохранения
            source_data (str): логи
            command (str): команда сканирования. на основе нее формируется имя файла

        Returns:
            bool: _description_
        """
        full_path = f'{path}/{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {command.replace("/", "_")}.{extension}'
        cls.logger.info('Save scan_data to file by path "%s"', full_path)
        try:
            async with aiofiles.open(full_path, 'wb' if isinstance(source_data, bytes) else 'w') as f:
                await f.write(source_data)
            return True
        except:
            cls.logger.error('Failed save source scan to path "%s" with error\n%s', full_path, traceback.format_exc())
            raise Exception('Failed save source scan to path "%s"' % full_path)


class MasscanScanner(ConsoleCommandExecutor):
    
    command = 'masscan'
    logger = get_logger(__package__, handlers=[])
    
    def __init__(self, target: List[Type[str]], interface_addr: str, ports: str=None, rate: int=None, source_port: int=None, timeout: int=None, interface: str=None,
                 only_open: bool=None, max_rate: int=None, ttl: int=None, retries: int=None, wait: int=10, ping: bool=False, format: str='oX') -> None:
        
        self.arguments = ListConsoleArgument()
        args = [{'argument': '-p', 'value': ports,},
                {'argument': '--rate', 'value': rate},
                {'argument': '--source-port', 'value': source_port},
                {'argument': '--connection-timeout', 'value': timeout},
                {'argument': '-e', 'value': interface},
                {'argument': '--open', 'value': only_open, 'is_flag': True},
                {'argument': '--max-rate', 'value': max_rate},
                {'argument': '--ttl', 'value': ttl},
                {'argument': '--retries', 'value': retries},
                {'argument': '--wait', 'value': wait},
                {'argument': 'target', 'value': target, 'is_flag': False, 'only_value': True},
                {'argument': '--ping', 'value': ping, 'is_flag': True},
                {'argument': f'-{format}', 'value': '-'},
                {'argument': '--adapter-ip', 'value': interface_addr}
                ]
        for i in args:
            self.arguments.append(ConsoleArgument(**i))
            
    async def async_execute(self, log_path: str = None) -> str:
        extentions = {'-oX': 'xml',
                      '-oL': 'list',
                      '-oJ': 'json'}
        extention = 'log'
        for i in self.arguments.list_args:
            if i.argument in list(extentions.keys()):
                extention = extentions[i.argument]
        res, err, code = await super().async_execute(log_path, extension=extention)
        if code != 0:
            raise SubrocessError(res, err, code)
        # ToDo check errors
        return res
    
    def sync_execute(self) -> str:
        res, err, code = super().sync_execute()
        if err or code != 0:
            raise SubrocessError(res, err, code)
        # ToDo check errors
        return res
        