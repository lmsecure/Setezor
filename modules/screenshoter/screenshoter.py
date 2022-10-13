from exceptions.loggers import LoggerNames
from exceptions.loggers import get_logger
from tools.shell_tools import create_async_shell_subprocess
import os
from time import time
import asyncio


class Screenshoter:
    def __init__(self, chromium_path):
        self.chromium_path = chromium_path
        self.options = ['--headless', '--disable-gpu', '--hide-scrollbars', '--mute-audio', '--disable-notifications',
		'--no-first-run', '--disable-crash-reporter', '--ignore-certificate-errors', '--incognito', '--disable-infobars',
        '--disable-sync', '--no-default-browser-check']
        
    async def take_screenshot_by_ip_port(self, ip: str, port: int, file_path: str, file_name: str,):
        url = f'https://{ip}:{port}'
        print(os.path.join(file_path, file_name))
        result, error = await (await create_async_shell_subprocess([self.chromium_path, *self.options, f'--screenshot={os.path.join(file_path, file_name)}', url])).communicate()
        print(result)
        print(error)
        
    async def take_screenshot_by_domain(self, domain: str, file_path: str, file_name: str,):
        url = f'https://{domain}'
        print(os.path.join(file_path, file_name))
        result, error = await (await create_async_shell_subprocess([self.chromium_path, *self.options, f'--screenshot={os.path.join(file_path, file_name)}', url])).communicate()
        print(result)
        print(error)