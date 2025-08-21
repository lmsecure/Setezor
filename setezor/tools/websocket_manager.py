
from setezor.patterns import singleton
from fastapi import WebSocket

from setezor.schemas.task import WebSocketMessage


@singleton
class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, entity_id: str, websocket: WebSocket):
        await websocket.accept()
        if self.active_connections.get(entity_id):
            self.active_connections[entity_id].append(websocket)
        else:
            self.active_connections[entity_id] = [websocket]

    def disconnect(self, entity_id: str, websocket: WebSocket):
        self.active_connections[entity_id].remove(websocket)
        if not self.active_connections[entity_id]:
            del self.active_connections[entity_id]

    async def send_message(self, entity_id: str, message: WebSocketMessage):
        for connection in self.active_connections.get(entity_id, []):
            await connection.send_text(message.model_dump_json())


WS_MANAGER = WebSocketManager()
WS_USER_MANAGER = WebSocketManager()