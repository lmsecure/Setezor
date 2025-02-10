import os
from random import randint
import hashlib

from fastapi import HTTPException
from setezor.models import Project, UserProject, Object, Agent, Invite_Link
from setezor.schemas.project import EnterTokenForm, SearchVulnsSetTokenForm
from setezor.services.invite_link_service import InviteLinkService
from setezor.tools.jwt import JWT_Tool
from setezor.unit_of_work import UnitOfWork
from setezor.settings import PATH_PREFIX, INVITE_LINK_EXPIRE_TIME
from setezor.models.base import generate_unique_id

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

            owner_role = await uow.role.find_one(name="owner")
            user_in_project_obj = UserProject(
                user_id=owner_id,
                project_id=new_project.id,
                role_id=owner_role.id
            )
            uow.user_project.add(user_in_project_obj.model_dump())

            object_model = Object(
                id=generate_unique_id(),
                project_id=new_project.id,
                critical_level=0
            )
            new_object = uow.object.add(object_model.model_dump())

            first_agent = Agent(
                name="Server",
                description="server",
                color="#" + hex(randint(0, 16777215))[2:].zfill(6),
                object_id=new_object.id,
                project_id=new_project.id,
                rest_url=os.environ.get("SERVER_REST_URL")
            )
            uow.agent.add(first_agent.model_dump())
            await uow.commit()
        ProjectFolders.create(project_id=project_id)

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
            if user_role_in_project.name != "owner":
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
    async def generate_invite_link(cls, uow: UnitOfWork, project_id: str):
        payload = {
            "project_id": project_id,
            "event": "enter"
        }
        return await InviteLinkService.create_token(uow=uow, payload=payload)
    
    @classmethod
    async def connect_new_user_to_project(cls, uow: UnitOfWork, 
                                          user_id: str, 
                                          enter_token_form: EnterTokenForm):
        async with uow:
            invite_link = await uow.invite_link.find_one(token_hash=enter_token_form.token, 
                                                         used=False)
        if not invite_link:
            raise HTTPException(status_code=400, detail="Token not found")
        token_payload = JWT_Tool.get_payload(invite_link.token)
        if not token_payload:
            raise HTTPException(status_code=403, detail="Token is expired")
        event = token_payload.get("event")
        if event == "enter":
            project_id = token_payload.get("project_id")
            async with uow:
                user_project = await uow.user_project.find_one(user_id=user_id, 
                                                               project_id=project_id)
            if user_project:
                raise HTTPException(status_code=400, detail="User is already in project")
            async with uow:
                viewer_role = await uow.role.find_one(name='viewer')
                new_user_in_project = UserProject(user_id=user_id,
                                                  project_id=project_id,
                                                  role_id=viewer_role.id)
                uow.user_project.add(new_user_in_project.model_dump())
                await uow.invite_link.edit_one(id=invite_link.id, data={"used": True})
                await uow.commit()
                return project_id
        raise HTTPException(status_code=400, detail="Invalid register token")

    
class ProjectFolders:
    @classmethod
    def create(cls, project_id: str):
        PROJECTS_PATH = cls.get_projects_path()
        if not os.path.exists(PROJECTS_PATH): 
            os.makedirs(PROJECTS_PATH, exist_ok=True)
        new_project_path = os.path.join(PROJECTS_PATH, project_id)
        if not os.path.exists(new_project_path): 
            os.makedirs(new_project_path, exist_ok=True)

    
    @classmethod
    def get_projects_path(cls):
        return os.path.abspath(os.path.join(PATH_PREFIX, 'projects'))
    
    @classmethod
    def get_path_for_project(cls, project_id: str):
        return os.path.join(cls.get_projects_path(), project_id)