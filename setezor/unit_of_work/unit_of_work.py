from setezor.repositories import \
    TasksRepository, \
    MACRepository, \
    IPRepository, \
    DNSRepository, \
    DNS_Type_Repository, \
    DomainRepository, \
    ObjectRepository, \
    RouteRepository, \
    RouteListRepository, \
    ProjectRepository, \
    ObjectTypeRepository, \
    PortRepository, \
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
    SoftwareRepository, \
    ASN_Repository, \
    VulnerabilityRepository, \
    ScopeRepository, \
    TargetRepository, \
    L4SoftwareRepository, \
    L4SoftwareVulnerabilityRepository, \
    VulnerabilityLinkRepository, \
    RoleRepository, \
    AuthLog_Repository, \
    InviteLinkRepository, \
    AuthenticationCredentialsRepository, \
    NodeCommentRepository, \
    ScanRepository, \
    L4SoftwareVulnerabilityScreenshotRepository, \
    NetworkSpeedTestRepository

from setezor.repositories import SQLAlchemyRepository
from sqlmodel.ext.asyncio.session import AsyncSession
from setezor.logger import logger
from setezor.repositories.agent_in_project_repository import AgentInProjectRepository
from setezor.repositories.agent_interface_repository import AgentInterfaceRepository
from setezor.repositories.agent_parent_agent_repository import AgentParentAgentRepository
from setezor.repositories.employee_email_repository import EmployeeEmailRepository
from setezor.repositories.employee_phone_repository import EmployeePhoneRepository
from setezor.repositories.employee_repository import EmployeeRepository
from setezor.repositories.network_port_software_vuln_comment_repository import \
    NetworkPortSoftwareVulnCommentRepository
from setezor.repositories.object_employee_repository import ObjectEmployeeRepository
from setezor.repositories.organization_department_repository import OrganizationDepartmentRepository
from setezor.repositories.organization_email_repository import OrganizationEmailRepository
from setezor.repositories.organization_phone_repository import OrganizationPhoneRepository
from setezor.repositories.organization_repository import OrganizationRepository
from setezor.repositories.setting_repository import SettingRepository
from setezor.repositories.software_type_repository import SoftwareTypeRepository
from setezor.repositories.software_version_repository import SoftwareVersionRepository
from setezor.repositories.dns_a_screenshot_repository import DNS_A_ScreenshotRepository
from setezor.repositories.web_archive_repository import WebArchiveRepository
from setezor.settings import DEV

class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory
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
        return DEV.mode

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
    def dns(self) -> DNSRepository: return DNSRepository(self.__session)

    @property
    def dns_type(self) -> DNS_Type_Repository: return DNS_Type_Repository(self.__session)

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
    def software(self) -> SoftwareRepository: return SoftwareRepository(self.__session)
    
    @property
    def software_type(self) -> SoftwareTypeRepository: return SoftwareTypeRepository(self.__session)
    
    @property
    def software_version(self) -> SoftwareVersionRepository: return SoftwareVersionRepository(self.__session)

    @property
    def vulnerability(self) -> VulnerabilityRepository: return VulnerabilityRepository(self.__session)

    @property
    def asn(self) -> ASN_Repository: return ASN_Repository(self.__session)

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
    def authentication_credentials(self) -> AuthenticationCredentialsRepository: return AuthenticationCredentialsRepository(self.__session)

    @property
    def invite_link(self) -> InviteLinkRepository: return InviteLinkRepository(self.__session)

    @property
    def auth_log(self) -> AuthLog_Repository: return AuthLog_Repository(self.__session)

    @property
    def node_comment(self) -> NodeCommentRepository: return NodeCommentRepository(self.__session)

    @property
    def l4_software_vulnerability_screenshot(self) -> L4SoftwareVulnerabilityScreenshotRepository: return L4SoftwareVulnerabilityScreenshotRepository(self.__session)

    @property
    def setting(self) -> SettingRepository: return SettingRepository(self.__session)

    @property
    def agent_in_project(self) -> AgentInProjectRepository: return AgentInProjectRepository(self.__session)
    
    @property
    def agent_parent_agent(self) -> AgentParentAgentRepository: return AgentParentAgentRepository(self.__session)

    @property
    def agent_interface(self) -> AgentInterfaceRepository: return AgentInterfaceRepository(self.__session)

    @property
    def network_speed_test(self) -> NetworkSpeedTestRepository: return NetworkSpeedTestRepository(self.__session)

    @property
    def dns_a_screenshot(self) -> DNS_A_ScreenshotRepository: return DNS_A_ScreenshotRepository(self.__session)

    @property
    def employee_email(self) -> EmployeeEmailRepository: return EmployeeEmailRepository(self.__session)

    @property
    def employee(self) -> EmployeeRepository: return EmployeeRepository(self.__session)

    @property
    def object_employee(self) -> ObjectEmployeeRepository: return ObjectEmployeeRepository(self.__session)

    @property
    def employee_phone(self) -> EmployeePhoneRepository: return EmployeePhoneRepository(self.__session)

    @property
    def network_port_software_vuln_comment(self) -> NetworkPortSoftwareVulnCommentRepository: return NetworkPortSoftwareVulnCommentRepository(self.__session)

    @property
    def organization_email(self) -> OrganizationEmailRepository: return OrganizationEmailRepository(self.__session)

    @property
    def organization(self) -> OrganizationRepository: return OrganizationRepository(self.__session)

    @property
    def organization_phone(self) -> OrganizationPhoneRepository: return OrganizationPhoneRepository(self.__session)

    @property
    def organization_department(self) -> OrganizationDepartmentRepository: return OrganizationDepartmentRepository(self.__session)

    @property
    def web_archive(self) -> WebArchiveRepository: return WebArchiveRepository(self.__session)

    def get_repo_by_model(self, model) -> SQLAlchemyRepository:
        for repository in SQLAlchemyRepository.__subclasses__():
            if repository.model is model:
                return repository(self.__session)
            repo = getattr(repository, 'model', None)
            if repo and repository.model.__name__ == type(model).__name__:
                return repository(self.__session)
