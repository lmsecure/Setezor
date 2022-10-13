from collections import namedtuple


Folders = namedtuple('Folders', ['nmap_logs', 'scapy_logs', 'screenshots'])
Files = namedtuple('Files', ['database_file', 'project_configs'])
Variables = namedtuple('Variables', ['iface', 'project_name'])

class FilesNames:
    nmap_logs = 'nmap_logs'
    scapy_logs = 'scapy_logs'
    screenshots = 'screenshots'
    database_file = 'database.sqlite'
    config_file = 'project_configs.json'
    