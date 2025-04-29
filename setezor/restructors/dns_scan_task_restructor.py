

from setezor.models.domain import Domain
from setezor.models.ip import IP
from setezor.models import IP, Domain, DNS_A as DNS_A_Model, \
    DNS_MX as DNS_MX_Model, DNS_NS as DNS_NS_Model,\
    DNS_CNAME as DNS_CNAME_Model, DNS_TXT as DNS_TXT_Model, \
    DNS_SOA as DNS_SOA_Model

class DNS_Scan_Task_Restructor:
    @classmethod
    async def restruct(cls, raw_result, domain_name: str):
        objects = []
        domain = Domain(domain=domain_name)
        objects.append(domain)
        for item in raw_result:
            record_type = item["record_type"]
            record_value = item["record_value"]
            models_for_this_dns = cls.get_models(record_type=record_type,
                                     record_value=record_value,
                                     target_domain=domain)
            objects.extend(models_for_this_dns)
        return objects
    

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