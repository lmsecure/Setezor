from fastapi import APIRouter, BackgroundTasks, Depends
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_user_id, role_required
from setezor.managers.agent_manager import AgentManager
from setezor.network_structures import InterfaceStruct
from setezor.services.agent_in_project_service import AgentInProjectService
from setezor.models import Agent
from setezor.schemas.agent import AgentAdd, AgentAddToProject, AgentColorChange, AgentDisplay, BackWardData, InterfaceOfAgent
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/agents_in_project",
    tags=["AgentsInProject"],
)


@router.get("")
async def agents(
    uow: UOWDep,
    user_id: str = Depends(get_user_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[dict]:
    agents = await AgentInProjectService.get_agents_for_tasks(uow=uow, project_id=project_id)
    return agents


@router.get("/settings")
async def agents_settings(
    uow: UOWDep,
    user_id: str = Depends(get_user_id),
    project_id: str = Depends(get_current_project),
) -> list[dict]:
    result = await AgentInProjectService.get_agents_in_project(uow=uow, project_id=project_id)
    return result

@router.get("/settings/possible_agents")
async def list_possible_agents(
    uow: UOWDep,
    user_id: str = Depends(get_user_id),
    project_id: str = Depends(get_current_project)
):
    result = await AgentInProjectService.possible_agents(uow=uow, user_id=user_id)
    return result

@router.patch("/settings/possible_agents")
async def list_possible_agents(
    uow: UOWDep,
    agents: AgentAddToProject,
    user_id: str = Depends(get_user_id),
    project_id: str = Depends(get_current_project)
):
    result = await AgentInProjectService.add_user_agents_to_project(uow=uow, agents=agents, user_id=user_id, project_id=project_id)
    return result

@router.get("/{id}/interfaces")
async def get_agent_interfaces(
    uow: UOWDep,
    id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> list[InterfaceStruct]:
    return await AgentInProjectService.get_interfaces(uow=uow, project_id=project_id, id=id)


@router.patch("/{id}/interfaces")
async def save_agent_interfaces(
    uow: UOWDep,
    id: str,
    interfaces: list[InterfaceOfAgent],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> bool:
    return await AgentInProjectService.save_interfaces(uow=uow, project_id=project_id, id=id, interfaces=interfaces)
    return False

@router.get("/{id}/remote_interfaces")
async def get_remote_agent_interfaces(
    uow: UOWDep,
    id: str,
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> list[InterfaceStruct]:
    return await AgentManager.get_interfaces_on_agent(uow=uow, project_id=project_id, agent_id_in_project=id, user_id=user_id)

@router.patch("/{agent_id}/update_color")
async def update_color(
    uow: UOWDep,
    agent_id: str,
    new_color: AgentColorChange,  # format: #xxxxxx
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> str:
    new_color = await AgentInProjectService.update_agent_color(uow=uow, project_id=project_id, agent_id=agent_id, color=new_color.color)
    return new_color