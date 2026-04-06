from setezor.models import Task
from setezor.schemas.task import WebSocketMessage
from setezor.signals.base_signal import Signal


class NotifySignal(Signal):

    async def __call__(self, data: dict, task: Task, **kwargs):
        message = WebSocketMessage(**data)
        await self.notify_by_websocket(message, task)