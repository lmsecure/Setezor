from typing import Annotated
from fastapi import APIRouter, Depends
from setezor.dependencies.project import get_current_project, get_user_id, role_required
from setezor.managers.agent_manager import AgentManager
from setezor.network_structures import InterfaceStruct
from setezor.services.agent_in_project_service import AgentInProjectService
from setezor.schemas.agent import AgentAddToProject, AgentColorChange, InterfaceOfAgent
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/agents_in_project",
    tags=["AgentsInProject"],
)


@router.get("")
async def agents(
    agents_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
    user_id: str = Depends(get_user_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[dict]:
    agents = await agents_in_project_service.get_agents_for_tasks(project_id=project_id)
    return agents


@router.get("/settings")
async def agents_settings(
    agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
    user_id: str = Depends(get_user_id),
    project_id: str = Depends(get_current_project),
) -> list[dict]:
    result = await agent_in_project_service.get_agents_in_project(project_id=project_id)
    return result

@router.get("/settings/possible_agents")
async def list_possible_agents(
    agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
    user_id: str = Depends(get_user_id),
    project_id: str = Depends(get_current_project)
):
    result = await agent_in_project_service.possible_agents(user_id=user_id)
    return result

@router.patch("/settings/possible_agents")
async def list_possible_agents(
    agents: AgentAddToProject,
    agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
    user_id: str = Depends(get_user_id),
    project_id: str = Depends(get_current_project)
):
    result = await agent_in_project_service.add_user_agents_to_project(agents=agents, user_id=user_id, project_id=project_id)
    return result

@router.get("/{id}/interfaces")
async def get_agent_interfaces(
    agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
    id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> list[InterfaceStruct]:
    return await agent_in_project_service.get_interfaces(project_id=project_id, id=id)


@router.patch("/{id}/interfaces")
async def save_agent_interfaces(
    agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
    id: str,
    interfaces: list[InterfaceOfAgent],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> bool:
    return await agent_in_project_service.save_interfaces(project_id=project_id, id=id, interfaces=interfaces)

@router.get("/{id}/remote_interfaces")
async def get_remote_agent_interfaces(
    agent_manager: Annotated[AgentManager, Depends(AgentManager.new_instance)],
    id: str,
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> list[InterfaceStruct]:
    return await agent_manager.get_interfaces_on_agent(project_id=project_id, agent_id_in_project=id, user_id=user_id)

@router.patch("/{agent_id}/update_color")
async def update_color(
    agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
    agent_id: str,
    new_color: AgentColorChange,  # format: #xxxxxx
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> str:
    new_color = await agent_in_project_service.update_agent_color(project_id=project_id, agent_id=agent_id, color=new_color.color)
    return new_color