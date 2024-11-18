import dns
import dns.asyncresolver
import asyncio
from typing import List,Dict
from setezor.exceptions.loggers import get_logger

logger = get_logger(__package__, handlers=[])

class DNS:
    @staticmethod
    async def query(domain:str):
        responses = await DNS.get_records(domain)
        return DNS.proceed_records(responses)

    @staticmethod
    def proceed_records(responses:List):
        domain_records = []
        for response in responses:
            if isinstance(response, tuple):
                rtype:str = response[0]
                answer:dns.resolver.Answer = response[1] # 'canonical_name', 'chaining_result', 'expiration', 'nameserver', 
                                                         # 'port', 'qname', 'rdclass', 'rdtype', 'response', 'rrset'
                rrsets = str(answer.rrset).split("\n")
                """
                    rrsets example: rrset ['lianmedia.ru. 1055 IN MX 10 mx1.hosting.reg.ru.', 'lianmedia.ru. 1055 IN MX 20 mx2.hosting.reg.ru.']
                """

                for rrset in rrsets:
                    record_value = rrset.split(f"IN {rtype} ")[1]
                    record_value = record_value.replace('"',"")
                    domain_records.append(
                    {
                        'record_type':rtype,
                        'record_value':record_value
                    }
                )
        return domain_records
    
    @classmethod
    async def resolve_domain(cls, domain:str,record:str): 
            #res = dns.asyncresolver.Resolver(configure=False)
            #res.nameservers = ["1.1.1.1"]
            #result = await res.resolve(qname = domain,rdtype=record)
            result = await dns.asyncresolver.resolve(qname = domain,rdtype=record)
            return record, result

    @classmethod
    async def get_records(cls, domain:str) -> List[Dict[str,str]]:
        """
            Получает список для ресурсных записей DNS, которые существуют у домена
        """
        
        logger.debug('Start getting DNS records for [%s]', domain)
        records = ["A","CNAME","MX","AAAA","SRV","TXT","NS","PTR","SOA"]
        tasks = []
        for record in records:
            task = asyncio.create_task(cls.resolve_domain(domain,record))
            tasks.append(task)
        return await asyncio.gather(*tasks,return_exceptions=True)    
