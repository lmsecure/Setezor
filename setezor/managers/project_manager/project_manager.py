import os
from random import randint
import uuid
from setezor.managers.task_manager import TaskManager
from setezor.models import Project, UserProject, Object, Agent
from setezor.schemas.project import SearchVulnsSetTokenForm
from setezor.unit_of_work import UnitOfWork
from .files import FilesStructure

class ProjectManager:

    @classmethod
    async def create_project(cls, uow: UnitOfWork, name: str, owner_id: str):
        id = uuid.uuid4().hex
        new_project = Project(
            id=id,
            name=name,
        )
        async with uow:
            new_project = await uow.project.add(new_project.model_dump())
            user_in_project_obj = UserProject(
                user_id=owner_id,
                project_id=new_project.id
            )
            await uow.user_project.add(user_in_project_obj.model_dump())
            await uow.commit()
            # ProjectFolders.create(id=id)


        async with uow:
            object = Object(
                project_id=new_project.id,
                critical_level=0
            )
            uow.session.add(object)
            await uow.commit()

            first_agent = Agent(
                project_id=new_project.id,
                name = "Server",
                description = "server",
                color = "#" + hex(randint(0, 16777215))[2:].zfill(6),
                object_id= object.id,
                rest_url = os.environ.get("SERVER_REST_URL")
            )
            uow.session.add(first_agent)
            await uow.commit()

        return new_project
    
    @classmethod
    async def get_by_id(cls, uow: UnitOfWork, project_id: str):
        async with uow:
            project = await uow.project.find_one(id=project_id)
            return project
        
    @classmethod
    async def delete_by_id(cls, uow: UnitOfWork, project_id: str):
        async with uow:
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
    
    
class ProjectFolders:
    @classmethod
    def create(cls, id: str):
        CURRENT_USER = os.path.expanduser('~')
        SETEZOR_DIR = '.local/share/setezor'
        PROJECTS_PATH = os.path.abspath(os.path.join(
            CURRENT_USER, SETEZOR_DIR, './projects/'))
        if not os.path.exists(PROJECTS_PATH):
            os.makedirs(PROJECTS_PATH, exist_ok=True)
        new_project_path = os.path.join(PROJECTS_PATH, id)
        FilesStructure.create_project_structure(new_project_path)
