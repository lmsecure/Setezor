import re
from setezor.tools.shell_tools import create_async_shell_subprocess


class NmapScanner:
    '''
    Класс-обертка над утилитой nmap
    '''
    
    def __init__(self, task = None):
        self.task = task

    start_command = ['nmap', '--privileged', '-oX', '-']
    superuser_permision = ['sudo', '-S']
      
    
    def _prepare_args(self, extra_args: str):
        bad_symbols = set(";|&$>#")
        index_bad_symbol = next((i for i, c in enumerate(extra_args) if c in bad_symbols), -1)
        if index_bad_symbol != -1:
            raise ValueError("Invalid character in command")
        args = [i for i in self.start_command + extra_args.split(' ') if i]
        # logger.debug('Start async nmap scan with command "%s"', ' '.join(args))
        return args
    
    def _check_results(self, args: list, result: str, error: str):
        if isinstance(error, bytes):
            error = error.decode()
        if isinstance(result, bytes):
            result = result.decode()
        error = ''.join([line for line in error.splitlines() if not any(keyword in line for keyword in ['NSOCK', 
                                                                                                        'INFO', 
                                                                                                        'MAC', 
                                                                                                        'DEBUG', 
                                                                                                        'WARNING',
                                                                                                        'Operation not permitted',
                                                                                                        'Offending packet',
                                                                                                        'Omitting future',
                                                                                                        ])])
        if not error or re.match(r'^\[sudo\] password for [^\n]+?$', error):
            return result
        # logger.error('Nmap sync scan failed with error\n%s', error)
        raise Exception(error)
    
    async def async_run(self, extra_args: str, _password: str):
        """Асинхронная реализация запуска nmap с заданными параметрами

        Args:
            extra_args (str): дополнительные параметры сканирования
            _password (str): пароль суперпользователя 

        Raises:
            NmapCommandError: _description_

        Returns:
            dict: логи nmap-а
        """
        args = self._prepare_args(extra_args=extra_args)
        # time1 = time()
        subprocess = await create_async_shell_subprocess(self.superuser_permision + args if _password else args)
        if self.task:
            self.task.pid = subprocess.pid
        result, error = await subprocess.communicate(_password)
        result = self._check_results(args=args, result=result, error=error)
        code = subprocess.returncode
        if code == -9:
            raise Exception("Process was killed")
        return result
        
