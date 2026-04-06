from types import TracebackType
from typing import Callable, Type, Any
from sqlmodel import SQLModel

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

class UnitOfWork:
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory
        self.__session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        if not self.__session:
            self.__session = self.session_factory()
        return self

    async def __aexit__(self, exc_type: Type[BaseException] | None, exc_value: BaseException | None, exc_traceback: TracebackType | None):
        if exc_type is not None:
            logger.error(str(exc_value), exc_info=True)
            await self.rollback()
        if self.__session is None:
            raise RuntimeError("Session is not initialized. Can't close")
        await self.__session.close()
        return False

    async def commit(self):
        if self.__session is None:
            raise RuntimeError("Session is not initialized. Can't commit")
        await self.__session.commit()

    async def flush(self):
        if self.__session is None:
            raise RuntimeError("Session is not initialized. Can't flush")
        await self.__session.flush()

    async def rollback(self):
        if self.__session is None:
            raise RuntimeError("Session is not initialized. Can't rollback")
        await self.__session.rollback()

    @property
    def session(self) -> AsyncSession:
        if self.__session is None:
            raise RuntimeError("Session is not initialized. Use 'async with UnitOfWork'")
        return self.__session

    @property
    def user(self) -> UserRepository: return UserRepository(self.session)

    @property
    def role(self) -> RoleRepository: return RoleRepository(self.session)

    @property
    def task(self) -> TasksRepository: return TasksRepository(self.session)

    @property
    def object_type(self) -> ObjectTypeRepository: return ObjectTypeRepository(self.session)

    @property
    def object(self) -> ObjectRepository: return ObjectRepository(self.session)

    @property
    def mac(self) -> MACRepository: return MACRepository(self.session)

    @property
    def ip(self) -> IPRepository: return IPRepository(self.session)

    @property
    def dns(self) -> DNSRepository: return DNSRepository(self.session)

    @property
    def dns_type(self) -> DNS_Type_Repository: return DNS_Type_Repository(self.session)

    @property
    def domain(self) -> DomainRepository: return DomainRepository(self.session)

    @property
    def route(self) -> RouteRepository: return RouteRepository(self.session)

    @property
    def route_list(self) -> RouteListRepository: return RouteListRepository(self.session)

    @property
    def project(self) -> ProjectRepository: return ProjectRepository(self.session)

    @property
    def user_project(self) -> UserProjectRepository: return UserProjectRepository(self.session)

    @property
    def port(self) -> PortRepository: return PortRepository(self.session)

    @property
    def cert(self) -> CertRepository: return CertRepository(self.session)

    @property
    def network(self) -> NetworkRepository: return NetworkRepository(self.session)

    @property
    def network_type(self) -> Network_Type_Repository: return Network_Type_Repository(self.session)

    @property
    def whois_domain(self) -> WhoisDomainRepository: return WhoisDomainRepository(self.session)

    @property
    def whois_ip(self) -> WhoisIPRepository: return WhoisIPRepository(self.session)

    @property
    def acunetix(self) -> AcunetixRepository: return AcunetixRepository(self.session)

    @property
    def agent(self) -> AgentRepository: return AgentRepository(self.session)

    @property
    def vendor(self) -> VendorRepository: return VendorRepository(self.session)

    @property
    def software(self) -> SoftwareRepository: return SoftwareRepository(self.session)

    @property
    def software_type(self) -> SoftwareTypeRepository: return SoftwareTypeRepository(self.session)

    @property
    def software_version(self) -> SoftwareVersionRepository: return SoftwareVersionRepository(self.session)

    @property
    def vulnerability(self) -> VulnerabilityRepository: return VulnerabilityRepository(self.session)

    @property
    def asn(self) -> ASN_Repository: return ASN_Repository(self.session)

    @property
    def scope(self) -> ScopeRepository: return ScopeRepository(self.session)

    @property
    def target(self) -> TargetRepository: return TargetRepository(self.session)

    @property
    def scan(self) -> ScanRepository: return ScanRepository(self.session)

    @property
    def l4_software(self) -> L4SoftwareRepository: return L4SoftwareRepository(self.session)

    @property
    def l4_software_vulnerability(self) -> L4SoftwareVulnerabilityRepository: return L4SoftwareVulnerabilityRepository(self.session)

    @property
    def vulnerability_link(self) -> VulnerabilityLinkRepository: return VulnerabilityLinkRepository(self.session)

    @property
    def authentication_credentials(self) -> AuthenticationCredentialsRepository: return AuthenticationCredentialsRepository(self.session)

    @property
    def invite_link(self) -> InviteLinkRepository: return InviteLinkRepository(self.session)

    @property
    def auth_log(self) -> AuthLog_Repository: return AuthLog_Repository(self.session)

    @property
    def node_comment(self) -> NodeCommentRepository: return NodeCommentRepository(self.session)

    @property
    def l4_software_vulnerability_screenshot(self) -> L4SoftwareVulnerabilityScreenshotRepository: return L4SoftwareVulnerabilityScreenshotRepository(self.session)

    @property
    def setting(self) -> SettingRepository: return SettingRepository(self.session)

    @property
    def agent_in_project(self) -> AgentInProjectRepository: return AgentInProjectRepository(self.session)

    @property
    def agent_parent_agent(self) -> AgentParentAgentRepository: return AgentParentAgentRepository(self.session)

    @property
    def agent_interface(self) -> AgentInterfaceRepository: return AgentInterfaceRepository(self.session)

    @property
    def network_speed_test(self) -> NetworkSpeedTestRepository: return NetworkSpeedTestRepository(self.session)

    @property
    def dns_a_screenshot(self) -> DNS_A_ScreenshotRepository: return DNS_A_ScreenshotRepository(self.session)

    @property
    def employee_email(self) -> EmployeeEmailRepository: return EmployeeEmailRepository(self.session)

    @property
    def employee(self) -> EmployeeRepository: return EmployeeRepository(self.session)

    @property
    def object_employee(self) -> ObjectEmployeeRepository: return ObjectEmployeeRepository(self.session)

    @property
    def employee_phone(self) -> EmployeePhoneRepository: return EmployeePhoneRepository(self.session)

    @property
    def network_port_software_vuln_comment(self) -> NetworkPortSoftwareVulnCommentRepository: return NetworkPortSoftwareVulnCommentRepository(self.session)

    @property
    def organization_email(self) -> OrganizationEmailRepository: return OrganizationEmailRepository(self.session)

    @property
    def organization(self) -> OrganizationRepository: return OrganizationRepository(self.session)

    @property
    def organization_phone(self) -> OrganizationPhoneRepository: return OrganizationPhoneRepository(self.session)

    @property
    def organization_department(self) -> OrganizationDepartmentRepository: return OrganizationDepartmentRepository(self.session)

    @property
    def web_archive(self) -> WebArchiveRepository: return WebArchiveRepository(self.session)

    def get_repo_by_model(self, model: Type[SQLModel]) -> SQLAlchemyRepository[Any] | None:
        for repository in SQLAlchemyRepository.__subclasses__():
            if repository.model is model:
                return repository(self.session)
            repo = getattr(repository, 'model', None)
            if repo and repository.model.__name__ == type(model).__name__:
                return repository(self.session)
