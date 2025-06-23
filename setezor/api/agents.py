from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends
from setezor.dependencies.project import get_current_project, get_user_id, role_required
from setezor.managers.agent_manager import AgentManager
from setezor.managers.task_manager import TaskManager
from setezor.services.agent_service import AgentService
from setezor.models import Agent
from setezor.schemas.agent import AgentAdd, AgentParents, BackWardData

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.get("/settings")
async def agents_settings(
    agent_service: Annotated[AgentService, Depends(AgentService.new_instance)],
    user_id: str = Depends(get_user_id),
) -> list[dict]:
    agents = await agent_service.settings_page(user_id=user_id)
    return agents


@router.post("", status_code=201)
async def create_agent(
    agent_service: Annotated[AgentService, Depends(AgentService.new_instance)],
    agent: AgentAdd,
    user_id: str = Depends(get_user_id),
) -> Agent:
    return await agent_service.create(agent=agent, user_id=user_id, gen_key=True)


@router.post("/{id}/connect")
async def connect_remote_agent(
    agent_manager: Annotated[AgentManager, Depends(AgentManager.new_instance)],
    id: str,
    user_id: str = Depends(get_user_id),
) -> None:
    agent = await agent_manager.connect_new_agent(agent_id=id, user_id=user_id)
    return agent

@router.get("/{id}/parents")
async def get_agent_parents(
    agent_service: Annotated[AgentService, Depends(AgentService.new_instance)],
    id: str,
    user_id: str = Depends(get_user_id),
) -> None:
    agent = await agent_service.parents_on_settings_page(agent_id=id, user_id=user_id)
    return agent

@router.patch("/{id}/parents")
async def set_agent_parents(
    agent_service: Annotated[AgentService, Depends(AgentService.new_instance)],
    id: str,
    parents: AgentParents,
    user_id: str = Depends(get_user_id),
) -> None:
    agent = await agent_service.set_parents_for_agent(agent_id=id, parents=parents, user_id=user_id)
    return agent


@router.post("/backward")
async def agents(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    data: BackWardData,
    background_tasks: BackgroundTasks,
) -> bool:
    background_tasks.add_task(task_manager.decipher_data_from_project_agent, data=data)
    return True
