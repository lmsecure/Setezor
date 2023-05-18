import asyncio
import os
from datetime import datetime
import asyncio
from time import time
from exceptions.loggers import get_logger
from tools.shell_tools import create_shell_subprocess, create_async_shell_subprocess



logger = get_logger(__package__, handlers=[])

class Screenshoter:
    def __init__(self, phantom_path: str, script_path: str):
        self.phantom_path = phantom_path
        self.script_path = script_path

    
    async def take_screenshot(self, folderpath: str, filename: str, schema: str = None, uri: str = '', port: int = None, domain: str = None, ip: str = None) -> list:
        urls = self._generate_url(domain=domain, ip=ip, port=port, schema=schema, uri=uri)
        res = []
        for url in urls:
            logger.debug('Start to take a screenshot from "%s"', url)
            time_of_scr_taken_start = time()
            screen_path = await self._take_screenshot(url=url, output_folderpath=folderpath, output_filename=filename)
            if screen_path:
                res.append(screen_path)
                logger.debug('Finish screnshot creation from "%s" after %.2f seconds', url, time() - time_of_scr_taken_start)
        return res
    
    async def _take_screenshot(self, url: str, output_folderpath: str, output_filename: str):  # ToDO add next params to phantom: timeout, screen_size and clip
        output_fullpath = os.path.join(output_folderpath, str(int(datetime.now().timestamp())) + '_' + output_filename)
        result, error = await (await create_async_shell_subprocess([self.phantom_path, self.script_path, url, output_fullpath, '2000'])).communicate()
        if error or 'ERROR' in result.decode():
            logger.debug('Cannot not take screenshot from "%s". Phantomjs say that: %s', url, error.decode() if error else result.decode())
            return None
        return output_fullpath
    
    def check_secure(self,):
        pass
    
    def _generate_url(self, ip: str = None, port: int = None, domain: str = None, schema: str = None, uri: str = '') -> list:
        def generate_schema(schema:str = None) -> tuple:
            if schema:
                return (schema,)
            else:
                return ('http', 'https')  # ToDo:  add to recognize secure protocol by port
        
        if ip and port:
            return [f'{i}://{ip}:{port}/{uri.lstrip("/")}' for i in generate_schema(schema)]
        elif domain and port:
            return [f'{i}://{domain}:{port}/{uri.lstrip("/")}' for i in generate_schema(schema)]
        elif domain:
            return [f'{i}://{domain}/{uri.lstrip("/")}' for i in generate_schema(schema)]
        else:
            raise Exception('Generation URL error: no domain, ip or port')