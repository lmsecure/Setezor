from setezor.db.database import async_session_maker
from setezor.interfaces import IUnitOfWork
from setezor.repositories import \
    TasksRepository, \
    MACRepository, \
    IPRepository, \
    DNS_A_Repository, \
    DNS_CNAME_Repository, \
    DNS_NS_Repository, \
    DNS_MX_Repository, \
    DNS_SOA_Repository, \
    DNS_TXT_Repository, \
    DomainRepository, \
    ObjectRepository, \
    RouteRepository, \
    RouteListRepository, \
    ProjectRepository, \
    ObjectTypeRepository, \
    PortRepository, \
    L7Repository, \
    CertRepository, \
    UserRepository, \
    NetworkRepository, \
    Network_Type_Repository, \
    UserProjectRepository, \
    AcunetixRepository, \
    WhoisDomainRepository, \
    WhoisIPRepository, \
    AgentRepository, \
    VendorRepository, \
    L7SoftwareRepository, \
    SoftwareRepository, \
    ASN_Repository, \
    L7SoftwareVulnerabilityRepository, \
    VulnerabilityRepository, \
    ScopeRepository, \
    TargetRepository, \
    L4SoftwareRepository, \
    L4SoftwareVulnerabilityRepository, \
    VulnerabilityLinkRepository, \
    RoleRepository, \
    AuthLog_Repository, \
    InviteLinkRepository, \
    L7AuthenticationCredentialsRepository, \
    NodeCommentRepository, \
    ScanRepository
    

from setezor.repositories import SQLAlchemyRepository
from sqlmodel.ext.asyncio.session import AsyncSession
from setezor.logger import logger

class UnitOfWork(IUnitOfWork):
    def __init__(self):
        self.session_factory = async_session_maker
        self.__session: AsyncSession = None

    async def __aenter__(self):
        if not self.__session:
            self.__session = self.session_factory()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            logger.error(exc_value)
            await self.rollback()
        await self.__session.close()
        return True

    async def commit(self):
        await self.__session.commit()

    async def flush(self):
        await self.__session.flush()

    async def rollback(self):
        await self.__session.rollback()

    @property
    def session(self) -> AsyncSession: return self.__session

    @property
    def user(self) -> UserRepository: return UserRepository(self.__session)

    @property
    def role(self) -> RoleRepository: return RoleRepository(self.__session)

    @property
    def task(self) -> TasksRepository: return TasksRepository(self.__session)

    @property
    def object_type(self) -> ObjectTypeRepository: return ObjectTypeRepository(self.__session)
    
    @property
    def object(self) -> ObjectRepository: return ObjectRepository(self.__session)

    @property
    def mac(self) -> MACRepository: return MACRepository(self.__session)

    @property
    def ip(self) -> IPRepository: return IPRepository(self.__session)

    @property
    def dns_a(self) -> DNS_A_Repository: return DNS_A_Repository(self.__session)
    
    @property
    def dns_mx(self) -> DNS_MX_Repository: return DNS_MX_Repository(self.__session)
    
    @property
    def dns_txt(self) -> DNS_TXT_Repository: return DNS_TXT_Repository(self.__session)
    
    @property
    def dns_ns(self) -> DNS_NS_Repository: return DNS_NS_Repository(self.__session)
    
    @property
    def dns_cname(self) -> DNS_CNAME_Repository: return DNS_CNAME_Repository(self.__session)
    
    @property
    def dns_soa(self) -> DNS_SOA_Repository: return DNS_SOA_Repository(self.__session)

    @property
    def domain(self) -> DomainRepository: return DomainRepository(self.__session)

    @property
    def route(self) -> RouteRepository: return RouteRepository(self.__session)

    @property
    def route_list(self) -> RouteListRepository: return RouteListRepository(self.__session)

    @property
    def project(self) -> ProjectRepository: return ProjectRepository(self.__session)
    
    @property
    def user_project(self) -> UserProjectRepository: return UserProjectRepository(self.__session)

    @property
    def port(self) -> PortRepository: return PortRepository(self.__session)
    
    @property
    def l7(self) -> L7Repository: return L7Repository(self.__session)
    
    @property
    def cert(self) -> CertRepository: return CertRepository(self.__session)
    
    @property
    def network(self) -> NetworkRepository: return NetworkRepository(self.__session)

    @property
    def network_type(self) -> Network_Type_Repository: return Network_Type_Repository(self.__session)

    @property
    def whois_domain(self) -> WhoisDomainRepository: return WhoisDomainRepository(self.__session)

    @property
    def whois_ip(self) -> WhoisIPRepository: return WhoisIPRepository(self.__session)

    @property
    def acunetix(self) -> AcunetixRepository: return AcunetixRepository(self.__session)

    @property
    def agent(self) -> AgentRepository: return AgentRepository(self.__session)
    
    @property
    def vendor(self) -> VendorRepository: return VendorRepository(self.__session)

    @property
    def L7Software(self) -> L7SoftwareRepository: return L7SoftwareRepository(self.__session)

    @property
    def software(self) -> SoftwareRepository: return SoftwareRepository(self.__session)

    @property
    def vulnerability(self) -> VulnerabilityRepository: return VulnerabilityRepository(self.__session)

    @property
    def asn(self) -> ASN_Repository: return ASN_Repository(self.__session)


    @property
    def vulnerability(self) -> VulnerabilityRepository: return VulnerabilityRepository(self.__session)
    
    @property
    def l7_software_vulnerability(self) -> L7SoftwareVulnerabilityRepository: return L7SoftwareVulnerabilityRepository(self.__session)

    @property
    def scope(self) -> ScopeRepository: return ScopeRepository(self.__session)
    
    @property
    def target(self) -> TargetRepository: return TargetRepository(self.__session)

    @property
    def scan(self) -> ScanRepository: return ScanRepository(self.__session)

    @property
    def l4_software(self) -> L4SoftwareRepository: return L4SoftwareRepository(self.__session)

    @property
    def l4_software_vulnerability(self) -> L4SoftwareVulnerabilityRepository: return L4SoftwareVulnerabilityRepository(self.__session)
    
    @property
    def vulnerability_link(self) -> VulnerabilityLinkRepository: return VulnerabilityLinkRepository(self.__session)

    @property
    def l7_authentication_credentials(self) -> L7AuthenticationCredentialsRepository: return L7AuthenticationCredentialsRepository(self.__session)

    @property
    def invite_link(self) -> InviteLinkRepository: return InviteLinkRepository(self.__session)
    
    @property
    def auth_log(self) -> AuthLog_Repository: return AuthLog_Repository(self.__session)
    
    @property
    def node_comment(self) -> NodeCommentRepository: return NodeCommentRepository(self.__session)

    def get_repo_by_model(self, model) -> SQLAlchemyRepository:
        for repository in SQLAlchemyRepository.__subclasses__():
            if repository.model is model:
                return repository(self.__session)
