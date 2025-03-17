from urllib.parse import urlparse
from ipaddress import IPv4Address


def parse_url(url:str) -> dict:
    parsed_url = urlparse(url)
    data = {}
    if parsed_url.port:
        data.update({"port": parsed_url.port})
    else:
        if parsed_url.scheme == "http":
            data.update({"port": 80})
        elif parsed_url.scheme == "https":
            data.update({"port": 443})
    try:
        IPv4Address(parsed_url.hostname)
        data.update({"ip": parsed_url.hostname})
    except:
        data.update({"domain": parsed_url.hostname})
    return data