from dns import resolver
import dns.asyncresolver
import asyncio
from typing import List, Dict

class DNS:
    @classmethod
    async def query(cls, domain: str):
        responses = await cls.get_records(domain)
        return cls.proceed_records(responses)

    @classmethod
    def proceed_records(cls, responses: List):
        domain_records = []
        for response in responses:
            if not isinstance(response, (resolver.NoAnswer, resolver.NoNameservers, resolver.LifetimeTimeout)):
                rtype: str = response[0]
                # 'canonical_name', 'chaining_result', 'expiration', 'nameserver',
                answer: resolver.Answer = response[1]
                # 'port', 'qname', 'rdclass', 'rdtype', 'response', 'rrset'
                rrsets = str(answer.rrset).split("\n")
                """
                    rrsets example: rrset ['lianmedia.ru. 1055 IN MX 10 mx1.hosting.reg.ru.', 'lianmedia.ru. 1055 IN MX 20 mx2.hosting.reg.ru.']
                """

                for rrset in rrsets:
                    record_value = rrset.split(f"IN {rtype} ")[1]
                    record_value = record_value.replace('"', "")
                    domain_records.append(
                        {
                            'record_type': rtype,
                            'record_value': record_value
                        }
                    )
        domain_records.sort(key=lambda x: x['record_value'])
        return domain_records

    @classmethod
    async def resolve_domain(cls, domain: str, record: str):
        # res = dns.asyncresolver.Resolver(configure=False)
        # res.nameservers = ["1.1.1.1"]
        # result = await res.resolve(qname = domain,rdtype=record)
        result = await dns.asyncresolver.resolve(qname=domain, rdtype=record)
        return record, result

    @classmethod
    async def get_records(cls, domain: str) -> List[Dict[str, str]]:
        """
            Получает список для ресурсных записей DNS, которые существуют у домена
        """

        # logger.debug('Start getting DNS records for [%s]', domain)
        records = ["A", "CNAME", "MX", "AAAA",
                   "SRV", "TXT", "NS", "PTR", "SOA"]
        tasks = []
        for record in records:
            task = asyncio.create_task(cls.resolve_domain(domain, record))
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=True)

