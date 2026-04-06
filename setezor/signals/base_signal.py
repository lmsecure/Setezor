from abc import ABC, abstractmethod
from typing import Callable

from setezor.data_writer.data_structure_service import DataStructureService
from setezor.models import Task
from setezor.services import AgentService, TasksService
from setezor.tools.file_manager import FileManager


class Signal(ABC):

    def __init__(
        self,
        tasks_service: TasksService,
        agent_service: AgentService,
        data_structure_service: DataStructureService,
        file_manager: FileManager,
        notify_by_websocket: Callable
    ):
        self.tasks_service = tasks_service
        self.agent_service = agent_service
        self.data_structure_service = data_structure_service
        self.file_manager = file_manager
        self.notify_by_websocket = notify_by_websocket

    @abstractmethod
    async def __call__(self, data: dict, task: Task = None, agent_id: str = None) -> None:
        raise NotImplementedError