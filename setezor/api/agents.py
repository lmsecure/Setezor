from fastapi import APIRouter, BackgroundTasks, Depends
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_user_id, role_required
from setezor.managers.agent_manager import AgentManager
from setezor.network_structures import InterfaceStruct
from setezor.services.agent_service import AgentService
from setezor.models import Agent
from setezor.schemas.agent import AgentAdd, AgentColorChange, AgentDisplay, AgentParents, BackWardData, InterfaceOfAgent
from setezor.schemas.roles import Roles

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.get("/settings")
async def agents_settings(
    uow: UOWDep,
    user_id: str = Depends(get_user_id),
) -> list[dict]:
    agents = await AgentService.settings_page(uow=uow, user_id=user_id)
    return agents


@router.post("")
async def create_agent(
    uow: UOWDep,
    agent: AgentAdd,
    user_id: str = Depends(get_user_id),
) -> Agent:
    agent = await AgentService.create(uow=uow, user_id=user_id, agent=agent)
    return agent


@router.post("/{id}/connect")
async def connect_remote_agent(
    uow: UOWDep,
    id: str,
    user_id: str = Depends(get_user_id),
) -> None:
    agent = await AgentManager.connect_new_agent(uow=uow, agent_id=id, user_id=user_id)
    return agent

@router.get("/{id}/parents")
async def get_agent_parents(
    uow: UOWDep,
    id: str,
    user_id: str = Depends(get_user_id),
) -> None:
    agent = await AgentService.parents_on_settings_page(uow=uow, agent_id=id, user_id=user_id)
    return agent

@router.patch("/{id}/parents")
async def set_agent_parents(
    uow: UOWDep,
    id: str,
    parents: AgentParents,
    user_id: str = Depends(get_user_id),
) -> None:
    agent = await AgentService.set_parents_for_agent(uow=uow, agent_id=id, parents=parents, user_id=user_id)
    return agent


@router.post("/backward")
async def agents(
    uow: UOWDep,
    data: BackWardData,
    background_tasks: BackgroundTasks,
) -> bool:
    background_tasks.add_task(
        AgentManager.decipher_data_from_project_agent, uow=uow, data=data)
    return True
