import asyncio

from fastapi.exceptions import HTTPException
from sqlmodel import SQLModel

from setezor.schemas.task import WebSocketMessage
from setezor.services.base_service import BaseService
from setezor.models.project import Project
from setezor.schemas.project import SearchVulnsSetTokenForm, ProjectDTO
from setezor.schemas.roles import Roles
from setezor.tools.websocket_manager import WS_USER_MANAGER


class ProjectService(BaseService):
    async def create(self, new_project: Project):
        async with self._uow:
            new_project_db = self._uow.project.add(new_project.model_dump())
            await self._uow.commit()
            return new_project_db
        
    async def get_by_id(self, project_id: str):
        async with self._uow:
            project = await self._uow.project.find_one(id=project_id)
            return project

    async def delete_by_id(self, user_id: str, project_id: str):
        async with self._uow:
            user_project = await self._uow.user_project.find_one(user_id=user_id, project_id=project_id)
            user_role_in_project = await self._uow.role.find_one(id=user_project.role_id)
            if user_role_in_project.name != Roles.owner:
                return False
            await self._uow.project.delete(id=project_id)
            await self._uow.commit()
            return True
        
    async def set_search_vulns_token(self, project_id: str, token_form: SearchVulnsSetTokenForm):
        async with self._uow:
            project = await self._uow.project.find_one(id=project_id)
            project.search_vulns_token = token_form.token
            await self._uow.commit()
        return None

    async def export_project(self, project_id: str) -> ProjectDTO:
        objects = {}
        async with self._uow:
            project = await self._uow.project.find_one(id=project_id)
            objects['Project'] = [project]

            agents_in_project = await self._uow.agent_in_project.get_project_agents(project_id=project_id)

            objects['Agent'] = []
            for agent_in_project in agents_in_project:
                agent = agent_in_project.agent
                agent.rest_url = ''
                agent.secret_key = ''
                agent.is_connected = False
                agent.flag = False

                objects['Agent'].append(agent_in_project.agent)

            objects['ParentAgent'] = await self._uow.agent_parent_agent.get_parent_agents_by_project(project_id=project_id)

            repos = [
                self._uow.user_project,  # user_project
                self._uow.scan,  # project_scan
                self._uow.object,  # object
                self._uow.agent_in_project,  # setezor_agent_in_project
                self._uow.asn,  # network_asn
                self._uow.network,  # network
                self._uow.mac,  # network_mac
                self._uow.ip,  # network_ip
                self._uow.domain,  # network_domain
                self._uow.dns,  # network_dns
                self._uow.screenshot,  # screenshot
                self._uow.dns_a_screenshot,  # network_dns_a_screenshot
                self._uow.port,  # network_port
                self._uow.vulnerability,  # software_vulnerability
                self._uow.software,  # setezor_d_software
                self._uow.l4_software,  # network_port_software
                self._uow.l4_software_vulnerability,  # network_port_software_vulnerability
                self._uow.l4_software_vulnerability_screenshot,  # network_port_software_vulnerability_screenshot
                self._uow.organization,  # organization
                self._uow.organization_email,  # organization_email,
                self._uow.organization_phone,  # organization_phone
                self._uow.organization_department,  # organization_department
                self._uow.employee,  # employee
                self._uow.employee_phone,  # employee_phone
                self._uow.employee_email,  # employee_email
                self._uow.route,  # network_route
                self._uow.route_list,  # network_route_list
                self._uow.task,  # project_task
                self._uow.whois_domain,  # software_web_whois_domain
                self._uow.authentication_credentials,  # software_authentication_credentials
                self._uow.network_speed_test,  # network_speed_test
                self._uow.cert,  # network_cert
                self._uow.whois_ip,  # software_web_whois_ip,
                self._uow.object_employee,  # object_employee
                self._uow.network_port_software_vuln_comment,  # network_port_software_vulnerability_comment
                self._uow.node_comment,  # network_ip_node_comment
                self._uow.scope,  # project_scope
                self._uow.target,  # project_scope_targets
                self._uow.vulnerability_link,  # software_vulnerability_link
            ]

            for repo in repos:
                obj_list_name = type(repo).__name__.replace('Repository', '')

                if obj_list_name == 'Software':
                    objects['SoftwareType'] = await self._uow.software_type.list()
                    objects['SoftwareVendor'] = await self._uow.software.get_software_vendors(project_id=project_id)
                    objects['Software'] = await self._uow.software.get_software_by_project(project_id=project_id)
                    objects['SoftwareVersion'] = await self._uow.software.get_software_versions(project_id=project_id)
                    continue

                if obj_list_name == 'MAC':
                    objects['Vendor'] = await self._uow.mac.get_mac_vendors(project_id=project_id)

                objects[obj_list_name] = await repo.filter_with_deleted_at(project_id=project_id)

            return ProjectDTO(name=project.name, data=objects)

    async def import_project(self, user_id: str, objects: dict[str, list[SQLModel]], imported_projects: set[str], hashed_data: str):
        async with self._uow:
            imported_project = objects['Project'][0]
            is_project_exists = await self._uow.project.find_one(id=imported_project.id, deleted_at=None)

        if is_project_exists:
            raise HTTPException(status_code=400, detail='Project already exists')

        asyncio.create_task(self.start_import_project(user_id, objects, imported_projects, hashed_data))

    async def start_import_project(self, user_id: str, objects: dict[str, list[SQLModel]], imported_projects: set[str], hashed_data: str):
        imported_project = objects['Project'][0]

        async with self._uow:
            current_project = await self._uow.project.find_one(id=imported_project.id)

            if current_project:
                await self._uow.project.edit_one(id=current_project.id, data={'deleted_at': None})

            all_user_agent = await self._uow.agent.list(user_id=user_id)
            current_server = await self._uow.agent.find_one(name='Server', secret_key='')
            imported_server = [agent for agent in objects['Agent'] if agent.name == 'Server'][0]

            imported_server_id = imported_server.id
            objects['Agent'].remove(imported_server)

            owner_role = await self._uow.role.find_one(name='owner')

            current_software_types = await self._uow.software_type.list()
            from_file_software_types = objects['SoftwareType']

            software_id_mapper = {}
            for from_file_software_type in from_file_software_types:
                for current_software_type in current_software_types:
                    if current_software_type.name == from_file_software_type.name:
                        software_id_mapper[from_file_software_type.id] = current_software_type.id

            await self._uow.commit()

        for objects_name, models_list in objects.items():
            async with self._uow:
                if not models_list:
                    continue

                id_set = set()
                for model in models_list:
                    id_set.add(model.id)
                    if 'user_id' in model.model_fields:
                        model.user_id = user_id
                    if 'role_id' in model.model_fields:
                        model.role_id = owner_role.id

                if objects_name == 'AgentInProject':
                    for agent_in_project in models_list:
                        if agent_in_project.agent_id == imported_server_id:
                            agent_in_project.agent_id = current_server.id

                if objects_name == 'Software':
                    for software in models_list:
                        if software_id_mapper.get(software.id):
                            software.id = software_id_mapper[software.id]

                if objects_name == 'ParentAgent':
                    for parent_agent in models_list:
                        if parent_agent.parent_agent_id not in all_user_agent:
                            parent_agent.parent_agent_id = current_server.id

                repo = self._uow.get_repo_by_model(models_list[0])

                await repo.add_many(models_list)
                await self._uow.commit()
                await repo.set_deleted_at(id_set)
                await self._uow.commit()

        if hashed_data in imported_projects:
            imported_projects.remove(hashed_data)
        message = WebSocketMessage(
            title='Import project',
            text='Project successfully imported',
            type='info',
            command='notify_user',
            user_id=user_id
        )
        await WS_USER_MANAGER.send_message(entity_id=user_id, message=message)
