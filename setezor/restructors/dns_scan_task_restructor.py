import json
import ipaddress

from setezor.models.domain import Domain
from setezor.models.ip import IP
from setezor.models import IP, Domain, DNS as DNS_Model
from setezor.db.entities import DNSTypes



class DNS_Scan_Task_Restructor:
    @classmethod
    async def restruct(cls, raw_result: list[dict], domain_name: str, **kwargs):
        objects = []
        target_domain_obj = Domain(domain=domain_name)
        objects.append(target_domain_obj)
        for item in raw_result:
            record_type = item.get("record_type")
            record_value = item.get("record_value")
            models_for_this_dns = cls.get_models(record_type=record_type,
                                                 record_value=record_value,
                                                 target_domain_obj=target_domain_obj)
            objects.extend(models_for_this_dns)
        return objects


    @classmethod
    def get_models(cls, record_type: str, record_value: str, target_domain_obj: Domain):
        if record_type not in DNSTypes.__members__:
            return []
        result = []
        dns_obj = DNS_Model(
            dns_type_id=DNSTypes[record_type]
            )
        match record_type:
            case DNSTypes.A.name:
                dns_obj.target_domain = target_domain_obj
                ip_obj = IP(ip=record_value)
                result.append(ip_obj)
                dns_obj.target_ip = ip_obj
            case DNSTypes.NS.name:
                dns_obj.target_domain = target_domain_obj
                new_domain = record_value.rstrip('.')
                new_domain_obj = Domain(domain=new_domain)
                result.append(new_domain_obj)
                dns_obj.value_domain = new_domain_obj
            case DNSTypes.MX.name:
                dns_obj.target_domain = target_domain_obj
                priority, domain_str = record_value.split()
                new_domain = ".".join(sub for sub in domain_str.split(".") if sub)
                new_domain_obj = Domain(domain=new_domain)
                result.append(new_domain_obj)
                dns_obj.value_domain = new_domain_obj
                dns_obj.extra_data = json.dumps({"priority" : int(priority)})
            case DNSTypes.CNAME.name:
                dns_obj.target_domain = target_domain_obj
                new_domain = record_value.rstrip('.')
                new_domain_obj = Domain(domain=new_domain)
                result.append(new_domain_obj)
                dns_obj.value_domain = new_domain_obj
            case DNSTypes.SOA.name:
                dns_obj.target_domain = target_domain_obj
                _nname, _rname, _serial, _refresh, _retry, _expire, _ttl = record_value.split(" ")
                new_domain_obj = Domain(domain=_nname.rstrip('.'))
                result.append(new_domain_obj)
                dns_obj.value_domain = new_domain_obj
                dns_obj.ttl = int(_ttl)
                dns_obj.extra_data = json.dumps(
                    {
                        "rname"   : _rname.rstrip('.'),
                        "serial"  : int(_serial),
                        "refresh" : int(_refresh),
                        "retry"   : int(_retry),
                        "expire"  : int(_expire)
                    }
                )
            case DNSTypes.TXT.name:
                dns_obj.target_domain = target_domain_obj
                dns_obj.extra_data = record_value
            case DNSTypes.SRV.name:
                dns_obj.target_domain = target_domain_obj
                _priority, _weight, _port, _target = record_value.split()
                new_domain_obj = Domain(domain=_target.rstrip('.'))
                result.append(new_domain_obj)
                dns_obj.value_domain = new_domain_obj
                dns_obj.extra_data = json.dumps(
                    {
                        "priority" : int(_priority),
                        "weight" : int(_weight),
                        "port" : int(_port)
                    }
                )
            case DNSTypes.PTR.name:
                dns_obj.target_domain = target_domain_obj
                ip, value_domain = record_value.split()
                ip_obj = IP(ip=ip)
                result.append(ip_obj)
                dns_obj.target_ip = ip_obj
                new_domain_obj = Domain(domain=value_domain.rstrip('.'))
                result.append(new_domain_obj)
                dns_obj.value_domain = new_domain_obj
            case DNSTypes.AAAA.name:
                # TODO: на данный момент отсутствует работа с IPv6
                # нужно сначала расширить валидацию для ip
                # затем доработать (если требуется) инструменты под IPv6

                # ip_obj = IP(ip=record_value)
                # result.append(ip_obj)
                # dns_obj.target_ip=ip_obj
                ...
            case _:
                return []
        result.append(dns_obj)
        return result
