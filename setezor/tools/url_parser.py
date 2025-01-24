from ipaddress import IPv4Address

def parse_url(url:str) -> dict:
    if "://" in url:
        _, addr_port = url.split("://")
    else:
        addr_port = url
    if ':' in addr_port:
        addr, port = addr_port.split(":")
        data = {"port": int(port)}
    else:
        addr = addr_port
        data = {"port": 443}
    try:
        IPv4Address(addr)
        data.update({"ip": addr})
    except:
        data.update({"domain": addr})
    return data