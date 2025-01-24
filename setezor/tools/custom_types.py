import asyncio
from fastapi import WebSocket
from typing import List, Dict, Any


class WebSocketQueue:
    def __init__(self, name: str):
        self.name = name
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self._websocket: WebSocket = None

    @property
    def websocket(self):
        return self._websocket

    @websocket.setter
    def websocket(self, web_socket):
        self._websocket = web_socket
        while not self.message_queue.empty():
            data = self.message_queue.get_nowait()
            loop = asyncio.get_running_loop()
            loop.run_until_complete(self.websocket.send_json(data))

    def put_item(self, message: Dict):
        self.message_queue.put_nowait(message)
        if self.websocket is not None:
            if not self.websocket.closed:
                while not self.message_queue.empty():
                    data = self.message_queue.get_nowait()
                    loop = asyncio.get_running_loop()
                    loop.run_until_complete(self.websocket.send_json(data))

    def stop_queue(self):
        pass  # Fixme implement method


class Clients:

    def __init__(self):
        self.clients: Dict[str, List[WebSocketQueue]] = {}

    def __len__(self):
        return len(self.clients)

    def get_client_queues(self, uuid: str) -> List[WebSocketQueue]:
        return self.clients.get(uuid)

    def get_queue(self, uuid: str, name: str) -> WebSocketQueue:
        for queue in self.clients.get(uuid, []):
            if queue.name == name:
                return queue
        raise Exception(f'Queue with name "{name}" not found')

    def delete_queues(self, uuid):
        self.clients.pop(uuid)  # FixMe need stop all jobs linked with queue?

    def is_exists(self, uuid):
        return uuid in self.clients.keys()

    def create_client(self, uuid: str):
        # FixMe add creation of the typical queues
        self.clients.update({uuid: [WebSocketQueue(name)
                            for name in ['task', 'message']]})
        return self

    def delete_client(self, uuid: str):
        client = self.clients.pop(uuid)
        for queue in client:
            queue.stop_queue()

    def __repr__(self):
        ws_count = 0
        for i in self.clients.items():
            ws_count += len(i)
        return f'<Clients count={len(self.clients)}, websocket={ws_count}>'


class MessageObserver:

    def __init__(self):
        self._websocket_queues: Dict[str, List[WebSocketQueue]] = {}

    def notify(self, message: dict, queue_type: str):
        for ws_queue in self._websocket_queues.get(queue_type, []):
            # FixMe take a slitting to queue by message type (from task and from other)
            ws_queue.put_item(message)

    def attach(self, ws_queue: WebSocketQueue):
        self._websocket_queues.setdefault(ws_queue.name, []).append(ws_queue)
        return self

    def attach_many(self, ws_queues: List[WebSocketQueue]):
        for queue in ws_queues:
            self.attach(ws_queue=queue)
        return self

    def detach(self, ws_queue: WebSocketQueue):
        for k, v in self._websocket_queues.items():
            try:
                v.remove(ws_queue)
            except ValueError:
                continue


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


@singleton
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        if not self.active_connections.get(project_id):
            self.active_connections[project_id] = {websocket}

    def disconnect(self, project_id, websocket: WebSocket):
        self.active_connections[project_id].remove(websocket)

    async def notify(self, project_id, message: dict[str, Any]):
        for connection in self.active_connections[project_id]:
            await connection.send_json(message)


connection_manager = ConnectionManager()
