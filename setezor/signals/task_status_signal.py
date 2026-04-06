from setezor.models import Task
from setezor.schemas.task import WebSocketMessage, TaskNotify
from setezor.signals.base_signal import Signal


class TaskStatusSignal(Signal):

    async def __call__(self, data: dict, task: Task, **kwargs):
        await self.tasks_service.set_status(
            id=task.id,
            status=data["status"],
            traceback=data["traceback"]
        )
        message = WebSocketMessage(
            title="Task status",
            text=TaskNotify(id=task.id, name=task.created_by, status=data["status"], traceback=data["traceback"]).to_str(),
            type=data["type"]
        )
        await self.notify_by_websocket(message, task)
