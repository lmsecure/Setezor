import json
from typing import List, Dict, Any, Set, Tuple
from setezor.models import Domain, IP, DNS
from setezor.db.entities import DNSTypes
from setezor.tools import ip_tools


class SdScanParser:
    @classmethod
    def parse(cls, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """Преобразует сырые данные в список валидных записей."""
        items = raw_data
        if raw_data and isinstance(raw_data, list) and isinstance(raw_data[0], list):
            items = raw_data[0]

        if not isinstance(items, list):
            return []

        result = []
        for item in items:
            if isinstance(item, dict) and item.get("domain") and isinstance(item.get("res"), list):
                result.append(item)
            elif isinstance(item, str):
                try:
                    entry = json.loads(item)
                    if isinstance(entry, dict) and entry.get("domain") and isinstance(entry.get("res"), list):
                        result.append(entry)
                except (json.JSONDecodeError, TypeError):
                    continue
        return result

    @classmethod
    def restructor(cls, data: List[Dict[str, Any]]) -> List[Any]:
        """Создаёт объекты Domain и DNS для каждой записи."""
        if not data:
            return []

        domains: Dict[str, Domain] = {}
        ips: Dict[str, IP] = {}
        dns_records: List[DNS] = []

        seen_dns_keys: Set[Tuple[str, str, str]] = set()

        for entry in data:
            domain_name = entry["domain"]
            
            # Создаём/получаем домен
            if domain_name not in domains:
                domains[domain_name] = Domain(domain=domain_name)

            domain_obj = domains[domain_name]

            for record in entry["res"]:
                host = record.get("host")
                if not host:
                    continue
                
                ttl = record.get("ttl", 0)

                if ip_tools.is_ip_address(host):
                    # IP-запись (тип A)
                    dns_key = ('A', domain_name, host)
                    if dns_key not in seen_dns_keys:
                        seen_dns_keys.add(dns_key)
                        
                        if host not in ips:
                            ips[host] = IP(ip=host)
                        ip_obj = ips[host]
                        
                        dns_records.append(
                            DNS(
                                target_domain=domain_obj,
                                target_ip=ip_obj,
                                dns_type_id=DNSTypes.A.value,
                                ttl=ttl
                            )
                        )
                else:
                    # Доменная запись (тип CNAME)
                    dns_key = ('CNAME', domain_name, host)
                    if dns_key not in seen_dns_keys:
                        seen_dns_keys.add(dns_key)
                        
                        if host not in domains:
                            domains[host] = Domain(domain=host)
                        value_domain_obj = domains[host]
                        
                        dns_records.append(
                            DNS(
                                target_domain=domain_obj,
                                value_domain=value_domain_obj,
                                dns_type_id=DNSTypes.CNAME.value,
                                ttl=ttl
                            )
                        )

        return list(domains.values()) + list(ips.values()) + dns_records