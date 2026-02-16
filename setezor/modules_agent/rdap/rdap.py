import aiohttp
from ipaddress import ip_address, ip_network
from typing import Optional, Dict, Any

class Rdap:

    HEADERS = {'Accept': 'application/rdap+json', 'User-Agent': 'osint-agent/1.0'}

    BOOTSTRAP_URLS = {
        'domain': 'https://data.iana.org/rdap/dns.json',
        'ipv4': 'https://data.iana.org/rdap/ipv4.json',
        'ipv6': 'https://data.iana.org/rdap/ipv6.json'
    }
     
    @classmethod
    async def find_rdap_url(cls, session: aiohttp.ClientSession, target: str):
        target = target.strip().lower()
        try:
            ip = ip_address(target)
            url_key = 'ipv4' if ip.version == 4 else 'ipv6'
            path = f"ip/{target}"
            async with session.get(cls.BOOTSTRAP_URLS[url_key], timeout=aiohttp.ClientTimeout(total=5)) as resp:
                resp.raise_for_status()
                bootstrap = await resp.json()
            for range_list, servers in bootstrap['services']:
                for cidr in range_list:
                    if ip in ip_network(cidr):
                        return servers[0] + path
            return None
        except ValueError:
            path = f"domain/{target}"
            tld = target.rstrip('.').split('.')[-1]
            if tld in ('ru', 'рф', 'xn--p1ai'):
                return f"https://cctld.ru/tci-ripn-rdap/{path}"
            async with session.get(cls.BOOTSTRAP_URLS['domain'], timeout=aiohttp.ClientTimeout(total=5)) as resp:
                resp.raise_for_status()
                bootstrap = await resp.json()
            for tlds, servers in bootstrap['services']:
                if tld in tlds:
                    return servers[0] + path
            return None
    
    @classmethod
    async def get_rdap_raw(cls, target: str): 
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(headers=cls.HEADERS, timeout=timeout) as session:
            rdap_url = await cls.find_rdap_url(session, target)
            if not rdap_url:
                return None

            try:
                async with session.get(rdap_url) as response:
                    response.raise_for_status()
                    data = await response.json()

                try:
                    ip_address(target.strip())
                    is_ip = True
                except ValueError:
                    is_ip = False

                if not is_ip:
                    registrar_url = None
                    for link in data.get("links", []):
                        if link.get("rel") in ("related", "registrar", "alternative"):
                            href = link.get("href")
                            if href and isinstance(href, str):
                                registrar_url = href.strip()
                                break

                    if registrar_url:
                        try:
                            if 'nic.ru' in registrar_url:
                                return data
                            async with session.get(registrar_url) as reg_resp:
                                reg_resp.raise_for_status()
                                return await reg_resp.json()
                        except Exception as e:
                            return data

                return data
            except Exception as e:
                return None
