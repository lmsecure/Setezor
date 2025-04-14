import os
from random import randint
import hashlib

from fastapi import HTTPException
from setezor.managers.project_manager.files import FilesStructure
from setezor.models import Project, UserProject, Object, Agent, AgentInProject, Domain, DNS_A
from setezor.models.agent_parent_agent import AgentParentAgent
from setezor.models.asn import ASN
from setezor.models.ip import IP
from setezor.models.mac import MAC
from setezor.models.network import Network
from setezor.models.scan import Scan
from setezor.schemas.project import EnterTokenForm, SearchVulnsSetTokenForm
from setezor.services.invite_link_service import InviteLinkService
from setezor.tools.ip_tools import get_network
from setezor.tools.jwt import JWT_Tool
from setezor.unit_of_work import UnitOfWork
from setezor.settings import PROJECTS_DIR_PATH
from setezor.models.base import generate_unique_id
from setezor.schemas.roles import Roles


class ProjectManager:

    @classmethod
    async def create_project(cls, uow: UnitOfWork, name: str, owner_id: str):
        async with uow:
            project_id = generate_unique_id()
            new_project_model = Project(
                id=project_id,
                name=name
            )
            new_project = uow.project.add(new_project_model.model_dump())

            owner_role = await uow.role.find_one(name=Roles.owner)
            user_in_project_obj = UserProject(
                user_id=owner_id,
                project_id=project_id,
                role_id=owner_role.id
            )
            uow.user_project.add(user_in_project_obj.model_dump())
            
            server_agent = await uow.agent.find_one(name="Server", secret_key="")
            
            obj_server_id, ag_server_id = generate_unique_id(), generate_unique_id()
            new_server_obj_model_in_project = Object(id=obj_server_id,
                                                     agent_id=ag_server_id,
                                                     project_id=project_id)

            uow.object.add(new_server_obj_model_in_project.model_dump())
            new_server_agent_in_project = AgentInProject(
                id=ag_server_id,
                object_id=new_server_obj_model_in_project.id,
                color="#" + hex(randint(0, 16777215))[2:].zfill(6),
                agent_id=server_agent.id,
                project_id=project_id
            )
            server_agent_in_project = uow.agent_in_project.add(new_server_agent_in_project.model_dump())
            

            first_synth_agent = Agent(
                id=generate_unique_id(),
                name="Synthetic",
                description="Not for active scans",
                rest_url="",
                user_id=owner_id,
                is_connected=True
            )
            uow.agent.add(first_synth_agent.model_dump())
            obj_id, ag_id = generate_unique_id(), generate_unique_id()
            new_obj_model = Object(id=obj_id,
                                   agent_id=ag_id,
                                   project_id=project_id)
            
            new_obj = uow.object.add(new_obj_model.model_dump())

            first_synth_agent_in_project = AgentInProject(
                id=ag_id,
                object_id=new_obj.id,
                name="Synthetic",
                description="Not for active scans",
                color="#" + hex(randint(0, 16777215))[2:].zfill(6),
                agent_id=first_synth_agent.id,
                parent_agent_id=server_agent_in_project.id,
                project_id=project_id
            )
            uow.agent_in_project.add(first_synth_agent_in_project.model_dump())


            agent_parent_agent = AgentParentAgent(
                agent_id=first_synth_agent.id,
                parent_agent_id=server_agent.id
            )
            uow.agent_parent_agent.add(agent_parent_agent.model_dump())
            new_asn = ASN(id=generate_unique_id(), 
                              project_id=project_id)
            uow.asn.add(new_asn.model_dump())
            new_network = Network(id=generate_unique_id(), 
                                start_ip="127.0.0.0", 
                                mask=24, 
                                project_id=project_id, 
                                asn_id=new_asn.id)
            uow.network.add(new_network.model_dump())

            new_mac = MAC(id=generate_unique_id(), 
                        mac="",
                        name="Default",
                        object_id=first_synth_agent_in_project.object_id,
                        project_id=project_id)
            uow.mac.add(new_mac.model_dump())

            new_ip = IP(id=generate_unique_id(),
                        ip="127.0.0.1", 
                        network_id=new_network.id, 
                        mac_id=new_mac.id, 
                        project_id=project_id)
            uow.ip.add(new_ip.model_dump())

            new_domain = Domain(id=generate_unique_id(),
                                project_id=project_id)
            uow.domain.add(new_domain.model_dump())

            new_dns_a = DNS_A(target_domain_id=new_domain.id, target_ip_id=new_ip.id, project_id=project_id)
            uow.dns_a.add(new_dns_a.model_dump())

            new_scan_model = Scan(
                id=generate_unique_id(),
                name="Initial scan",
                project_id=project_id
            )
            new_scan = uow.scan.add(new_scan_model.model_dump())

            ProjectFolders.create(project_id=project_id)
            project_path = ProjectFolders.get_path_for_project(project_id=project_id)
            scan_project_path = os.path.join(project_path, new_scan.id)
            FilesStructure.create_project_structure(scan_project_path)

            await uow.commit()

        return new_project
    
    @classmethod
    async def get_by_id(cls, uow: UnitOfWork, project_id: str):
        async with uow:
            project = await uow.project.find_one(id=project_id)
            return project
        
    @classmethod
    async def delete_by_id(cls, uow: UnitOfWork, user_id: str, project_id: str):
        async with uow:
            user_project = await uow.user_project.find_one(user_id=user_id, project_id=project_id)
            user_role_in_project = await uow.role.find_one(id=user_project.role_id)
            if user_role_in_project.name != Roles.owner:
                return False
            await uow.project.delete(id=project_id)
            await uow.commit()
            return True
        
    @classmethod
    async def set_search_vulns_token(cls, uow: UnitOfWork, project_id: str, token_form: SearchVulnsSetTokenForm):
        async with uow:
            project = await uow.project.find_one(id=project_id)
            project.search_vulns_token = token_form.token
            await uow.commit()
        return None
    
    @classmethod
    async def generate_invite_link(cls, uow: UnitOfWork, 
                                   count_of_entries: int, 
                                   project_id: str):
        payload = {
            "project_id": project_id,
            "event": "enter"
        }
        return await InviteLinkService.create_token(uow=uow, 
                                                    count_of_entries=count_of_entries, 
                                                    payload=payload)
    
    @classmethod
    async def connect_new_user_to_project(cls, uow: UnitOfWork, 
                                          user_id: str, 
                                          enter_token_form: EnterTokenForm):
        async with uow:
            invite_link = await uow.invite_link.find_one(token_hash=enter_token_form.token)
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
            async with uow:
                user_project = await uow.user_project.find_one(user_id=user_id, 
                                                               project_id=project_id)
            if user_project:
                raise HTTPException(status_code=400, detail="User is already in project")
            async with uow:
                viewer_role = await uow.role.find_one(name=Roles.viewer)
                new_user_in_project = UserProject(user_id=user_id,
                                                  project_id=project_id,
                                                  role_id=viewer_role.id)
                uow.user_project.add(new_user_in_project.model_dump())
                await uow.invite_link.edit_one(id=invite_link.id, data={"count_of_entries": invite_link.count_of_entries-1})
                await uow.commit()
                return project_id
        raise HTTPException(status_code=400, detail="Invalid register token")

    
class ProjectFolders:
    @classmethod
    def create(cls, project_id: str):
        new_project_path = cls.get_path_for_project(project_id=project_id)
        if not os.path.exists(new_project_path):
            os.makedirs(new_project_path, exist_ok=True)

    @classmethod
    def get_projects_path(cls):
        return PROJECTS_DIR_PATH

    @classmethod
    def get_path_for_project(cls, project_id: str):
        PROJECTS_PATH = cls.get_projects_path()
        new_project_path = os.path.join(PROJECTS_PATH, project_id)
        if not os.path.exists(new_project_path):
            os.makedirs(new_project_path, exist_ok=True)
        return new_project_path