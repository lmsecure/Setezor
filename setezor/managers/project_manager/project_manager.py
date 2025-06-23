import os
from random import randint
from typing import Annotated

from fastapi import Depends, HTTPException
from setezor.managers.project_manager.files import FilesStructure, ProjectFolders
from setezor.models import Project, UserProject, Object, Agent, AgentInProject, Domain, DNS_A
from setezor.models.agent_parent_agent import AgentParentAgent
from setezor.models.asn import ASN
from setezor.models.ip import IP
from setezor.models.mac import MAC
from setezor.models.network import Network
from setezor.models.scan import Scan
from setezor.schemas.project import EnterTokenForm, ProjectCreateForm
from setezor.services.agent_in_project_service import AgentInProjectService
from setezor.services.agent_parent_agent_service import AgentParentAgentService
from setezor.services.agent_service import AgentService
from setezor.services.asn_service import AsnService
from setezor.services.dns_a_service import DNS_A_Service
from setezor.services.domain_service import DomainsService
from setezor.services.invite_link_service import InviteLinkService
from setezor.services.ip_service import IPService
from setezor.services.mac_service import MacService
from setezor.services.network_service import NetworkService
from setezor.services.object_service import ObjectService
from setezor.services.project_service import ProjectService
from setezor.services.role_service import RoleService
from setezor.services.scan_service import ScanService
from setezor.services.user_project_service import UserProjectService
from setezor.tools.ip_tools import get_network
from setezor.tools.jwt import JWT_Tool
from setezor.unit_of_work import UnitOfWork

from setezor.models.base import generate_unique_id
from setezor.schemas.roles import Roles


class ProjectManager:
    def __init__(
        self,
            project_service: ProjectService,
            user_project_service: UserProjectService,
            agent_service: AgentService,
            role_service: RoleService,
            agent_in_project_service: AgentInProjectService,
            object_service: ObjectService,
            agent_parent_agent_service: AgentParentAgentService,
            asn_service: AsnService,
            network_service: NetworkService,
            mac_service: MacService,
            ip_service: IPService,
            domain_service: DomainsService,
            dns_a_service: DNS_A_Service,
            scan_service: ScanService,
            invite_link_service: InviteLinkService
    ):
        self.__project_service: ProjectService = project_service
        self.__user_project_service: UserProjectService = user_project_service
        self.__agent_service: AgentService = agent_service
        self.__role_service: RoleService = role_service
        self.__agent_in_project_service: AgentInProjectService = agent_in_project_service
        self.__object_service: ObjectService = object_service
        self.__agent_parent_agent_service: AgentParentAgentService = agent_parent_agent_service
        self.__invite_link_service: InviteLinkService = invite_link_service
        self.__asn_service: AsnService = asn_service
        self.__network_service: NetworkService = network_service
        self.__mac_service: MacService = mac_service
        self.__ip_service: IPService = ip_service

        self.__domain_service: DomainsService = domain_service
        self.__dns_a_service: DNS_A_Service = dns_a_service
        self.__scan_service: ScanService = scan_service

    async def create_project(self, new_project_form: ProjectCreateForm, owner_id: str):
        new_project = await self.__project_service.create(Project(
            name=new_project_form.name
        ))
        owner_role = await self.__role_service.get_by_name(name=Roles.owner)

        user_in_project = await self.__user_project_service.create(UserProject(
            user_id=owner_id,
            project_id=new_project.id,
            role_id=owner_role.id
        ))
        server_agent = await self.__agent_service.get_server_agent()

        server_agent_in_project_id = generate_unique_id()

        new_server_obj = await self.__object_service.create(Object(agent_id=server_agent_in_project_id,
                                                                   project_id=new_project.id))

        new_server_agent_in_project = await self.__agent_in_project_service.create(AgentInProject(
            id=server_agent_in_project_id,
            object_id=new_server_obj.id,
            color="#" + hex(randint(0, 16777215))[2:].zfill(6),
            agent_id=server_agent.id,
            project_id=new_project.id
        ))

        new_synth_agent = await self.__agent_service.create(Agent(
            name="Synthetic",
            description="Not for active scans",
            rest_url="",
            is_connected=True
        ), user_id=owner_id)

        new_obj = await self.__object_service.create(Object(agent_id=new_synth_agent.id,
                                                            project_id=new_project.id))

        synth_agent_in_project = await self.__agent_in_project_service.create(AgentInProject(
            object_id=new_obj.id,
            name="Synthetic",
            description="Not for active scans",
            color="#" + hex(randint(0, 16777215))[2:].zfill(6),
            agent_id=new_synth_agent.id,
            parent_agent_id=new_server_agent_in_project.id,
            project_id=new_project.id
        ))

        agent_parent_agent = await self.__agent_parent_agent_service.create(AgentParentAgent(
            agent_id=new_synth_agent.id,
            parent_agent_id=server_agent.id
        ))

        new_asn = await self.__asn_service.create(ASN(id=generate_unique_id(),
                                                      project_id=new_project.id))

        new_network = await self.__network_service.create(Network(start_ip="127.0.0.0",
                                                          mask=24,
                                                          project_id=new_project.id,
                                                          asn_id=new_asn.id))

        new_mac = await self.__mac_service.create(MAC(mac="",
                                                      name="Default",
                                                      object_id=synth_agent_in_project.object_id,
                                                      project_id=new_project.id))

        new_ip = await self.__ip_service.create(IP(ip="127.0.0.1",
                                                   network_id=new_network.id,
                                                   mac_id=new_mac.id,
                                                   project_id=new_project.id))

        new_domain = await self.__domain_service.create(Domain(project_id=new_project.id))

        new_dns_a = await self.__dns_a_service.create(DNS_A(target_domain_id=new_domain.id,
                                                            target_ip_id=new_ip.id,
                                                            project_id=new_project.id))

        new_scan = await self.__scan_service.create(
            project_id=new_project.id,
            scan=Scan(
                name="Initial scan",
                project_id=new_project.id
            ))

        ProjectFolders.create(project_id=new_project.id)
        project_path = ProjectFolders.get_path_for_project(
            project_id=new_project.id)
        scan_project_path = os.path.join(project_path, new_scan.id)
        FilesStructure.create_project_structure(scan_project_path)

        return new_project

    async def connect_new_user_to_project(self,
                                          user_id: str,
                                          enter_token_form: EnterTokenForm):
        invite_link = await self.__invite_link_service.get_by_hash(
            token_hash=enter_token_form.token)
        if not invite_link:
            raise HTTPException(status_code=400, detail="Token not found")
        token_payload = JWT_Tool.get_payload(invite_link.token)
        if not token_payload:
            raise HTTPException(status_code=403, detail="Token is expired")
        if not invite_link.count_of_entries:
            raise HTTPException(status_code=403, detail="Invalid token")
        event = token_payload.get("event")
        if event == "enter":
            project_id = token_payload.get("project_id")
            user_project = await self.__user_project_service.get_user_project(user_id=user_id,
                                                                        project_id=project_id)
            if user_project:
                raise HTTPException(
                    status_code=400, detail="User is already in project")
            viewer_role = await self.__role_service.get_by_name(name=Roles.viewer)
            new_user_in_project = await self.__user_project_service.create(UserProject(user_id=user_id,
                                                                                 project_id=project_id,
                                                                                 role_id=viewer_role.id))
            await self.__invite_link_service.change_count_of_entries(
                token_id=invite_link.id,
                new_count_of_entries=invite_link.count_of_entries-1
            )
            return project_id
        raise HTTPException(status_code=400, detail="Invalid register token")

    @classmethod
    async def new_instance(
        cls,
        project_service: Annotated[ProjectService, Depends(ProjectService.new_instance)],
        user_project_service:  Annotated[UserProjectService, Depends(UserProjectService.new_instance)],
        agent_service:  Annotated[AgentService, Depends(AgentService.new_instance)],
        role_service:  Annotated[RoleService, Depends(RoleService.new_instance)],
        agent_in_project_service:  Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
        object_service:  Annotated[ObjectService, Depends(ObjectService.new_instance)],
        agent_parent_agent_service:  Annotated[AgentParentAgentService, Depends(AgentParentAgentService.new_instance)],
        asn_service:  Annotated[AsnService, Depends(AsnService.new_instance)],
        network_service:  Annotated[NetworkService, Depends(NetworkService.new_instance)],
        mac_service:  Annotated[MacService, Depends(MacService.new_instance)],
        ip_service:  Annotated[IPService, Depends(IPService.new_instance)],
        domain_service:  Annotated[DomainsService, Depends(DomainsService.new_instance)],
        dns_a_service:  Annotated[DNS_A_Service, Depends(DNS_A_Service.new_instance)],
        scan_service:  Annotated[ScanService, Depends(ScanService.new_instance)],
        invite_link_service:  Annotated[InviteLinkService, Depends(InviteLinkService.new_instance)]
    ):
        
        return cls(
            project_service=project_service,
            user_project_service=user_project_service,
            agent_service=agent_service,
            role_service=role_service,
            agent_in_project_service=agent_in_project_service,
            object_service=object_service,
            agent_parent_agent_service=agent_parent_agent_service,
            asn_service=asn_service,
            network_service=network_service,
            mac_service=mac_service,
            ip_service=ip_service,
            domain_service=domain_service,
            dns_a_service=dns_a_service,
            scan_service=scan_service,
            invite_link_service=invite_link_service
        )
