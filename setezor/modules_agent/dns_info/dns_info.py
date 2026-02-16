import ipaddress
import dns.asyncresolver
import asyncio



class DNS:

    # TODO: возможно, в дальнейшем, можно добавить еще (соответственно нужно будет добавить обработчики под них, на сервере):
    #    CAA - контроль SSL-сертификатов.
    #  NAPTR - маршрутизация сервисов (SIP, ENUM, XMPP).
    #     DS - хэш от DNSSEC-ключа (связь с родителем).
    # DNSKEY - публичные ключи DNSSEC.
    #  DMARC - политика почты (через TXT).
    __allowed_records = {"A", "CNAME", "MX", "AAAA", "SRV", "TXT", "NS", "PTR", "SOA"}


    @classmethod
    async def query(cls, target: str, ns_servers: list[str] = None,  records: list[str] | None = None):
        target_ip = None
        try:
            ipaddress.ip_address(target)
            target_ip = target
            target = str(dns.reversename.from_address(target))
        except ValueError:
            pass  # target is domain (no ip)
        responses = await cls.get_records(domain = target, ns_servers=ns_servers, records=records)
        result = cls.proceed_records(responses, target_domain=target.rstrip('.'), target_ip=target_ip)
        data = {
            "domain_name": target.rstrip('.'),
            "raw_result": result
        }
        return data


    @classmethod
    def proceed_records(cls, responses: list, target_domain: str, target_ip: str = None):
        domain_records = []
        for response in responses:
            if isinstance(response, Exception):
                continue
            rtype: str = response[0]
            answer = response[1]
            rrsets = str(answer.rrset).split("\n")
            for rrset in rrsets:
                record_value = rrset.split(f"IN {rtype} ")[1]
                record_value = record_value.replace('"', "")
                if target_ip:
                    record_value = target_ip + " " + record_value
                domain_records.append(
                    {
                        'record_type': rtype,
                        'record_value': record_value,
                        'target_value': target_domain
                    }
                )
        domain_records.sort(key=lambda x: x['record_value'])
        return domain_records


    @classmethod
    async def resolve_domain(cls, domain: str, record: str, ns_servers: list[str] | None = None):
        resolver = dns.asyncresolver.Resolver()
        tcp = False
        if ns_servers:
            tcp = True
            resolver.nameservers = ns_servers
        result = await resolver.resolve(qname=domain, rdtype=record, tcp=tcp)
        return record, result


    @classmethod
    async def get_records(cls, domain: str, ns_servers: list[str] | None = None, records: list[str] | None = None) -> list[dict[str, str]]:
        """
            Получает список для ресурсных записей DNS, которые существуют у домена
        """
        if not records:
            records = cls.__allowed_records
        else:
            records = [record for record in records if record.upper() in cls.__allowed_records]
        tasks = []
        for record in records:
            task = asyncio.create_task(cls.resolve_domain(domain, record, ns_servers=ns_servers))
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=True)
