from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from setezor.dependencies.project import get_user_id
from setezor.managers.agent_manager import AgentManager
from setezor.managers.task_manager import TaskManager
from setezor.managers.module_manager import ModuleManager
from setezor.services.agent_service import AgentService
from setezor.schemas.agent import AgentUpdate, InterfaceOfAgent
from setezor.network_structures import InterfaceStruct
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


@router.patch("/{agent_id}", status_code=200)
async def update_agent(
    agent_id: str,
    agent_service: Annotated[AgentService, Depends(AgentService.new_instance)],
    agent: AgentUpdate,
    user_id: str = Depends(get_user_id),
):
    return await agent_service.update(agent=agent, agent_id=agent_id, user_id=user_id)


@router.get("/{id}/heirs")
async def agent_heirs(
    agent_service: Annotated[AgentService, Depends(AgentService.new_instance)],
    id: str,
    user_id: str = Depends(get_user_id)
) -> list[dict]:
    return await agent_service.get_all_heirs(user_id=user_id, agent_id=id)


@router.delete("/delete")
async def delete_agent(
    agent_service: Annotated[AgentService, Depends(AgentService.new_instance)],
    agent_ids: list[str],
    user_id: str = Depends(get_user_id)
) -> None:
    await agent_service.delete(user_id=user_id, agent_ids = agent_ids)


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

@router.get("/{agent_id}/remote_interfaces")
async def get_remote_agent_interfaces(
    agent_manager: Annotated[AgentManager, Depends(AgentManager.new_instance)],
    agent_id: str,
    user_id: str = Depends(get_user_id)
) -> list[InterfaceStruct]:
    return await agent_manager.get_interfaces_on_agent(user_id=user_id, agent_id=agent_id)

@router.patch("/{agent_id}/interfaces")
async def save_agent_interfaces(
    agent_manager: Annotated[AgentManager, Depends(AgentManager.new_instance)],
    agent_id: str,
    interfaces: list[InterfaceOfAgent],
    user_id: str = Depends(get_user_id)
) -> bool:
    return await agent_manager.save_interfaces(user_id=user_id, agent_id=agent_id, interfaces=interfaces)

@router.post("/backward")
async def agents(
    request: Request,
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    agent_manager: Annotated[AgentManager, Depends(AgentManager.new_instance)],
    data: BackWardData,
    background_tasks: BackgroundTasks,
) -> bool:
    if not data.data and not await agent_manager.is_agent_exist(agent_id=data.sender):
        raise HTTPException(status_code=404, detail=f'Agent {data.sender} {request.client.host} '
                                                    f'trying to connect, but not registered...')
    background_tasks.add_task(task_manager.decipher_data_from_project_agent, data=data)
    return True


@router.get("/get_module/{agent_id}/{module_name}")
async def get_module(
    agent_id: str,
    module_name: str,
    module_manager: Annotated[ModuleManager, Depends(ModuleManager.new_instance)],
) -> StreamingResponse:
    return await module_manager.get_module(agent_id=agent_id, module_name=module_name)


@router.get("/show_available_modules/{agent_id}")
async def show_available_modules(
    agent_id: str,
    module_manager: Annotated[ModuleManager, Depends(ModuleManager.new_instance)],
    user_id: str = Depends(get_user_id),
):
    modules = await module_manager.get_available_modules(agent_id=agent_id, user_id=user_id)
    return modules
