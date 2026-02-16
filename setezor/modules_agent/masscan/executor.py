from dataclasses import dataclass
from typing import List, Type
from subprocess import Popen, PIPE
from setezor.tools.shell_tools import create_async_shell_subprocess
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

async def create_async_shell(command: list):
    execute_command = ' '.join(command)
    bad_symbols = set(";|&$>#")
    index_bad_symbol = next((i for i, c in enumerate(execute_command) if c in bad_symbols), -1)
    if index_bad_symbol != -1:
        raise ValueError("Invalid character in command")
    return await create_async_shell_subprocess(command)



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
    # logger: Logger
    
    
    def __init__(self) -> None:
        self.arguments = ListConsoleArgument()
    
    def prepare_command(self):
        if len(self.arguments):
            pass
        else:
            raise Exception(f'Command "{self.command}" have no arguments')
    
    
    async def async_execute(self, log_path: str=None, extension: str='log'):
        self.arguments.clear_empty_args()
        execution_command = self.arguments.prepare_command(self.command)
        process = await create_async_shell(execution_command)
        if self.task:
            self.task.pid = process.pid
        result, error = await process.communicate()
        result = result.decode(encoding='utf8', errors='backslashreplace')
        error = error.decode(encoding='utf8', errors='backslashreplace')
        code= process.returncode
        return result, error, code


class MasscanScanner(ConsoleCommandExecutor):
    
    command = 'masscan'
    # logger = get_logger(__package__, handlers=[])
    
    def __init__(self, target: List[Type[str]], interface_addr: str, task = None, ports: str=None, rate: int=None, source_port: int=None, timeout: int=None, interface: str=None, search_udp_port: bool=False,
                 only_open: bool=None, max_rate: int=None, ttl: int=None, retries: int=None, wait: int=10, ping: bool=False, format: str='oX') -> None:
        
        self.arguments = ListConsoleArgument()
        self.task = task
        args = [{'argument': '--rate', 'value': rate},
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
        if search_udp_port:
            args.insert(0, {'argument': '-p', 'value': 'U:' + ports.replace(',', ',U:')})
        else:
            args.insert(0, {'argument': '-p', 'value': ports })

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
        if code == -2: # SIGINT
            return res
        if code != 0:
            raise SubrocessError(res, err, code)
        # ToDo check errors
        return res
    
