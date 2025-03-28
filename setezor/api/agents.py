from fastapi import APIRouter, BackgroundTasks, Depends
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_user_id, role_required
from setezor.managers.agent_manager import AgentManager
from setezor.network_structures import InterfaceStruct
from setezor.services.agent_service import AgentService
from setezor.models import Agent
from setezor.schemas.agent import AgentAdd, AgentColorChange, BackWardData, InterfaceOfAgent
from setezor.schemas.roles import Roles

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.get("")
async def agents(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[Agent]:
    agents = await AgentService.list(uow=uow, project_id=project_id)
    return agents


@router.get("/settings")
async def agents_settings(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[dict]:
    agents = await AgentService.settings_page(uow=uow, project_id=project_id)
    return agents


@router.post("")
async def create_agent(
    uow: UOWDep,
    agent: AgentAdd,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> Agent:
    agent = await AgentService.create(uow=uow, project_id=project_id, agent=agent)
    return agent


@router.post("/{id}/connect")
async def connect_remote_agent(
    uow: UOWDep,
    id: str,
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    agent = await AgentManager.connect_new_agent(uow=uow, project_id=project_id, agent_id=id, user_id=user_id)
    return agent


@router.post("/backward")
async def agents(
    uow: UOWDep,
    data: BackWardData,
    background_tasks: BackgroundTasks,
) -> bool:
    background_tasks.add_task(
        AgentManager.decipher_data_from_agent, uow=uow, data=data)
    return True


@router.get("/{id}/remote_interfaces")
async def get_remote_agent_interfaces(
    uow: UOWDep,
    id: str,
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> list[InterfaceStruct]:
    return await AgentManager.get_interfaces_on_agent(uow=uow, project_id=project_id, agent_id=id, user_id=user_id)


@router.get("/{id}/interfaces")
async def get_agent_interfaces(
    uow: UOWDep,
    id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> list[InterfaceStruct]:
    return await AgentService.get_interfaces(uow=uow, project_id=project_id, id=id)


@router.patch("/{id}/interfaces")
async def save_agent_interfaces(
    uow: UOWDep,
    id: str,
    interfaces: list[InterfaceOfAgent],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> bool:
    return await AgentService.save_interfaces(uow=uow, project_id=project_id, id=id, interfaces=interfaces)


@router.patch("/{agent_id}/update_color")
async def update_color(
    uow: UOWDep,
    agent_id: str,
    new_color: AgentColorChange,  # format: #xxxxxx
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> str:
    new_color = await AgentService.update_agent_color(uow=uow, project_id=project_id, agent_id=agent_id, color=new_color.color)
    return new_color
