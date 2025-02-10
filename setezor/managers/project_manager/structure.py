import enum

class Folders(enum.Enum):
    nmap_logs_path = "nmap_logs"
    scapy_logs_path = "scapy_logs"
    masscan_logs_path = "masscan_logs"
    cve_logs_path = "cve_logs"
    whois_logs_path = "whois_logs_path"
    certificates_path = "certificates"
    screenshots_path = "screenshots"

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
