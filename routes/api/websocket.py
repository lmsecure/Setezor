from aiohttp.web import Request, Response, json_response, WebSocketResponse
from aiohttp import WSMsgType
from routes.session import project_require, get_db_by_session, set_websocket_to_client_queue
from routes.api.base_web_view import BaseView


class WebSocketView(BaseView):
    endpoint = '/websocket'
     
    @BaseView.route('GET', '/{name}')
    async def websocket(self, request: Request):
        queue_name = request.match_info.get('name')
        ws = WebSocketResponse()
        await ws.prepare(request)
        await set_websocket_to_client_queue(request=request, websocket=ws, queue_name=queue_name)
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s' % ws.exception())
        return ws