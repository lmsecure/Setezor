import aiodns
import random
import string
import asyncio
import os
from base64 import b64decode



class Domain_brute:

    @classmethod
    async def query(cls, name: str, dict_file: str | None = None, query_type: str = "A") -> list[str]:
        """
            Отправляет запросы на dns сервера с заданным доменом
            по записи 'A'. Возвращает все найденные доменные имена
        """
        async def resolve(resolver: aiodns.DNSResolver, subdomain: str, name: str, query_type: str):
            URL = f"{subdomain}.{name}"
            return URL, await resolver.query(URL,query_type)


        async def resolve_domain(sem: asyncio.Semaphore, resolver: aiodns.DNSResolver, subdomain: str, name: str, query_type: str = "A"):
            async with sem:
                return await resolve(resolver, subdomain, name, query_type)

        subdomains = cls.get_subdomains_from_file(file=dict_file)
        resolver = aiodns.DNSResolver(loop=asyncio.get_event_loop())
        sem = asyncio.Semaphore(10)
        test_subdomains = [
            ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
            for _ in range(5)
        ]

        test_tasks = [
            asyncio.create_task(resolve_domain(sem, resolver, sd, name, query_type))
            for sd in test_subdomains
        ]
        test_responses = await asyncio.gather(*test_tasks, return_exceptions=True)

        valid_count = sum(
            1 for r in test_responses
            if not isinstance(r, Exception) and not isinstance(r, aiodns.error.DNSError)
        )

        if valid_count >= 5:
            raise Exception('Wildcard resolution is enabled on this domain')

        tasks = []
        sem = asyncio.Semaphore(100)
        for subdomain in subdomains:
            task = asyncio.create_task(resolve_domain(sem, resolver, subdomain, name, query_type))
            tasks.append(task)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        result = []
        for response in responses:
            if not isinstance(response, aiodns.error.DNSError):
                domain, answers = response
                records = [{'host': r.host, 'ttl': r.ttl} for r in answers]
                result.append({"domain": domain, "res": records})
        return result


    @classmethod
    def get_subdomains_from_file(cls, file: str | None) -> set[str]:
        if file:
            data = b64decode(file.split(',')[1]).decode()
            return set(data.splitlines())
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "subdomains.txt")
        with open(file_path,'r') as file:
            return set(file.read().splitlines())
