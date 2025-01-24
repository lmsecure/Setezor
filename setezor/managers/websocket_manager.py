
from setezor.patterns import singleton
from fastapi import WebSocket

from setezor.schemas.task import WebSocketMessage

@singleton
class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        if self.active_connections.get(project_id):
            self.active_connections[project_id].append(websocket)
        else:
            self.active_connections[project_id] = [websocket]

    def disconnect(self, project_id: str, websocket: WebSocket):
        self.active_connections[project_id].remove(websocket)
        if not self.active_connections[project_id]:
            del self.active_connections[project_id]

    async def send_message(self, project_id: str, message: WebSocketMessage):
        for connection in self.active_connections.get(project_id, []):
            await connection.send_text(message.model_dump_json())



WS_MANAGER = WebSocketManager()