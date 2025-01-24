from dns import resolver
import dns.asyncresolver
import asyncio
from typing import List, Dict
from setezor.models import IP, Domain, DNS_A as DNS_A_Model, \
DNS_MX as DNS_MX_Model, DNS_NS as DNS_NS_Model,\
DNS_CNAME as DNS_CNAME_Model, DNS_TXT as DNS_TXT_Model, \
DNS_SOA as DNS_SOA_Model

class DNS:
    @classmethod
    async def query(cls, domain: str):
        responses = await cls.get_records(domain)
        return cls.proceed_records(domain, responses)

    @classmethod
    def proceed_records(cls, domain_name: str, responses: List):
        domain_records = []
        for response in responses:
            if not isinstance(response, (resolver.NoAnswer, resolver.NoNameservers)):
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
        objects = []
        domain = Domain(domain=domain_name)
        objects.append(domain)
        for item in domain_records:
            record_type = item["record_type"]
            record_value = item["record_value"]
            models_for_this_dns = cls.get_models(record_type=record_type,
                                     record_value=record_value,
                                     target_domain=domain)
            objects.extend(models_for_this_dns)
        return objects

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

    @classmethod
    def get_models(cls, record_type:str, record_value: str, target_domain: Domain):
        ip = IP()
        match record_type:
            case "A":
                ip.ip = record_value
                return [ip, DNS_A_Model(target_ip=ip,
                                        target_domain=target_domain)]
            case "MX":
                priority_str, domain_str = record_value.split(" ")
                priority = int(priority_str)
                domain_value = ".".join(sub for sub in domain_str.split(".") if sub)
                domain = Domain(domain=domain_value)
                return [ip, domain, DNS_MX_Model(
                    target_ip=ip,
                    target_domain=target_domain,
                    value_domain=domain,
                    priority=priority
                )]
            case "CNAME":
                return DNS_CNAME_Model
            case "NS":
                domain_value = ".".join(sub for sub in record_value.split(".") if sub)
                domain = Domain(domain=domain_value)
                return [ip, domain, DNS_NS_Model(
                    target_ip=ip,
                    target_domain=target_domain,
                    value_domain=domain
                )]
            case "TXT":
                return [ip, DNS_TXT_Model(target_ip=ip,
                                          target_domain=target_domain,
                                          record_value=record_value)]
            case "SOA":
                NNAME_str, RNAME_str, SERIAL, REFRESH_str, RETRY_str, EXPIRE_str, TTL_str = record_value.split(" ")
                NNAME = ".".join(sub for sub in NNAME_str.split(".") if sub)
                RNAME = ".".join(sub for sub in RNAME_str.split(".") if sub)
                REFRESH = int(REFRESH_str)
                RETRY = int(RETRY_str)
                EXPIRE = int(EXPIRE_str)
                TTL = int(TTL_str)
                domain_nname = Domain(domain=NNAME)
                domain_rname = Domain(domain=RNAME)
                return [ip, domain_nname, domain_rname, DNS_SOA_Model(target_ip=ip,
                                          target_domain=target_domain,
                                          domain_nname=domain_nname,
                                          domain_rname=domain_rname,
                                          serial=SERIAL,
                                          refresh=REFRESH,
                                          retry=RETRY,
                                          expire=EXPIRE,
                                          ttl=TTL)]
            case _:
                return []
