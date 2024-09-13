import aiodns
import asyncio
import os
from setezor.exceptions.loggers import get_logger
from typing import List

logger = get_logger(__package__, handlers=[])

class Domain_brute:
    @classmethod
    async def query(cls, name:str, query_type:str = "A") -> List[str]:
        """
            Отправляет запросы на dns сервера с заданным доменом
            по записи 'A'. Возвращает все найденные доменные имена
        """
        async def resolve(resolver:aiodns.DNSResolver,subdomain:str,name:str,query_type:str):
            URL = f"{subdomain}.{name}"
            return URL, await resolver.query(URL,query_type)

        async def resolve_domain(sem:asyncio.Semaphore,resolver:aiodns.DNSResolver,subdomain:str,name:str,query_type:str="A"):
            async with sem:
                return await resolve(resolver,subdomain,name,query_type)
            
        logger.debug('Start domain_brute [%s]', name)    
        resolver = aiodns.DNSResolver(loop=asyncio.get_event_loop())
        filename = cls.get_subdomains_file_path()
        with open(filename,'r') as file:
            subdomains = file.read().splitlines()
        tasks = []
        sem = asyncio.Semaphore(100)
        for subdomain in subdomains:
            task = asyncio.create_task(resolve_domain(sem,resolver,subdomain,name,query_type))
            tasks.append(task)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        result = set()
        for response in responses:
            if not isinstance(response, aiodns.error.DNSError):
                result.add(response[0])
        return list(result)

    @classmethod
    def get_subdomains_file_path(cls, filename:str = "subdomains.txt") -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename)
        return file_path