import enum


class Schedulers(enum.Enum):
    scapy = "scapy"
    nmap = "nmap"
    masscan = "masscan"
    cve_vulners = "cve_vulners"
    cve_nvd = "cve_nvd"
    snmp = "snmp"
    whois = "whois"
    cert_info = "cert_info"
    dns_info = "dns_info"
    sd_find = "sd_find"
    other = "other"
    search_vulns = "search_vulns"
    screenshoter = "screenshoter"
