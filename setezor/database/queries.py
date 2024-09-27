
from . import queries_files as qf
from .db_connection import DBConnection


class Queries:
    """Класс управления запросами к базе
    """
    def __init__(self, db_path: str):
        """Инициализация объекта управления запросам
        хранит в себе запросы  в иерархическом виде

        Args:
            db_path (str): путь до базы
        """
        self.db = DBConnection(db_path)
        self.object = qf.ObjectQueries(session_maker=self.db.create_session())
        self.object_types = qf.ObjectTypeQueries(session_maker=self.db.create_session())
        self.mac = qf.MACQueries(objects=self.object, session_maker=self.db.create_session())
        self.ip = qf.IPQueries(mac=self.mac, session_maker=self.db.create_session())
        self.port = qf.PortQueries(ip=self.ip, session_maker=self.db.create_session())
        self.software = qf.SoftwareQueries(session_maker = self.db.create_session())
        self.task = qf.TaskQueries(session_maker=self.db.create_session())
        self.screenshot = qf.ScreenshotQueries(task=self.task, port=self.port, session_maker=self.db.create_session())
        self.network = qf.NetworkQueries(ip_queries=self.ip, session_maker=self.db.create_session())
        self.agent = qf.AgentQueries(session_maker=self.db.create_session())
        self.route = qf.RouteQueries(session_maker=self.db.create_session())
        self.route_list = qf.RouteListQueries(session_maker=self.db.create_session())
        self.pivot = qf.PivotResourceSoftwareQueries(session_maker=self.db.create_session())
        self.domain = qf.DomainQueries(ip = self.ip, session_maker=self.db.create_session())
        self.whois = qf.WhoisQueries(domain = self.domain, ip = self.ip, session_maker=self.db.create_session())
        self.DNS = qf.DNSQueries(domain = self.domain, session_maker=self.db.create_session())
        self.Cert = qf.CertQueries(domain = self.domain, ip = self.ip, session_maker=self.db.create_session()) # ???
        self.resource = qf.ResourceQueries(ip = self.ip, port=self.port, domain=self.domain, session_maker=self.db.create_session())
        self.vulnerability = qf.VulnerabilityQueries(session_maker = self.db.create_session())
        self.vuln_res_soft = qf.VulnerabilityResSoftQueries(session_maker = self.db.create_session())
        self.resource_software = qf.ResourceSoftwareQueries(resource=self.resource, software=self.software, session_maker = self.db.create_session())
        self.vulnerability_link = qf.VulnerabilityLinkQueries(session_maker = self.db.create_session())

        self.pivot_ip_mac_port = qf.PivotIpMacPortQueries(session_maker = self.db.create_session())
        self.pivot_domain_ip = qf.PivotDomainIP(session_maker = self.db.create_session())
        self.pivot_software_vulnerability_link = qf.PivotSoftwareVulnerabilityLink(session_maker = self.db.create_session())