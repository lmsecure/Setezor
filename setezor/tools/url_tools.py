from ipaddress import IPv4Address

def parse_url(url: str) -> dict:
    _, addr_port = url.split("://")
    if ':' in addr_port:
        addr, port_and_path = addr_port.split(":")
        if "/" in port_and_path:
            port, *paths = port_and_path.split('/')[0]
        else:
            port = port_and_path
        data = {"port": int(port)}
    else:
        addr = addr_port.split("/")[0]
        data = {}
    try:
        IPv4Address(addr)
        data.update({"ip": addr})
    except:
        data.update({"domain": addr})
    return data