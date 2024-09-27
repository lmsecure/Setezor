import asyncio
import aiohttp
import json

from typing import Literal

from datetime import datetime
from time import time


from setezor.exceptions.loggers import get_logger
logger = get_logger(__package__)


class CveCrawler():

    async def scan(self) -> dict:
        start_time = time()
        logger.debug('Start CveCrawler with url "%s"', self.get_url())
        result = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.get_url()) as response:
                if response.status == 200:
                    result = await response.json()
                logger.debug('Finish CveCrawler after %.2f seconds', time() - start_time)
                return result


    @staticmethod
    def save_source_data(full_path: str, log: dict):
        with open(full_path, 'wb' if isinstance(log, bytes) else 'w') as f:
            f.write(json.dumps(log, indent=4))

    def get_url(self):
        match self.__class__.__name__:
            case "CveVulnersCrawler":
                return ''.join([self.server, self.endpoint, self.cpe])
            case "CveNVDCrawler":
                ...
    

    def scan_and_save(self, full_path) -> bool:
        loop = asyncio.get_event_loop()
        log = loop.run_until_complete(self.scan())
        if log:
            self.save_source_data(full_path, log)
            return True
        return False


    @classmethod
    def run(cls, project_path: str, cpe: str, source: Literal['vulners', 'nvd'] | None = None):
        if source not in ['vulners', 'nvd', None]: source = None
        match source:
            case 'vulners':
                tmp = CveVulnersCrawler(cpe)
                full_path = f'{project_path}/{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {tmp.__class__.__name__} {cpe}.json'
                status = tmp.scan_and_save(full_path)
                return (None, full_path)[status]
            case 'nvd':
                tmp = CveNVDCrawler(cpe)
                full_path = f'{project_path}/{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {tmp.__class__.__name__} {cpe}.json'
                status = tmp.scan_and_save(full_path)
                return (None, full_path)[status]
            case _:
                for _cls in cls.__subclasses__():
                    tmp = _cls(cpe)
                    full_path = f'{project_path}/{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {tmp.__class__.__name__} {cpe}.json'
                    tmp.scan_and_save(full_path)


class CveVulnersCrawler(CveCrawler):
    server = "https://vulners.com"
    endpoint = "/api/v3/burp/software/?software="
    def __init__(self, cpe):
        self.cpe = cpe

class CveNVDCrawler(CveCrawler):
    server = "https://services.nvd.nist.gov"
    endpoint = "/rest/json/cves/2.0?&cpeName="
    def __init__(self, cpe):
        self.cpe = cpe