from functools import lru_cache
from ipaddress import IPv4Address, IPv4Interface

from aiohttp.web import Request, Response, json_response
from pydantic import BaseModel, ValidationError, ConfigDict

from app_routes.session import project_require, get_db_by_session, get_project
from app_routes.api.base_web_view import BaseView
from modules.application import PMRequest

from tools.json_tools import orjson_dumps
from network_structures import RouteStruct, IPv4Struct

from database.queries_files.route_queries import (VisNode, 
                                                  VisIcon, 
                                                  GATEWAY_ICON,
                                                  AGENT_ICON,
                                                  VisEdge)
from database.models import IP

class DeleteEdgeRequest(BaseModel):
    
    """Реквест удаления связи, принимает идешники ip адресов"""
    from_ip: int
    to_ip: int

class CreateEdgeRequest(BaseModel):
    
    """Реквест создания связи, принимает идешники ip адресов"""
    
    from_ip: int
    to_ip: int
    agent_id: int


class RouteView(BaseView):
    endpoint = "/route"
    queries_path = "route"

    @BaseView.route("get", "/vis_edges")
    @project_require
    async def get_vis_edges(self, request: PMRequest):
        db = await get_db_by_session(request)
        edges = db.route.get_vis_edges()
        return json_response([i.model_dump(by_alias=True) for i in edges], dumps=orjson_dumps)
    
    @BaseView.route("get", "/vis_nodes")
    @project_require
    async def get_vis_nodes(self, request: PMRequest):
        
        db = await get_db_by_session(request)
        nodes = db.route.get_vis_nodes()
        nodes = [i.model_dump() for i in nodes]
        return json_response(nodes, dumps=orjson_dumps)
     
    @BaseView.route("put", "/create_edge")
    @project_require
    async def create_edge(self, request: PMRequest):
        
        db = await get_db_by_session(request)
        try:
            create_request = CreateEdgeRequest.model_validate_json(await request.read())
        except ValidationError as e:
            return Response(body=e.json(), status=423)
        
        from_ip = db.ip.get_by_id(id=create_request.from_ip)
        to_ip = db.ip.get_by_id(id=create_request.to_ip)
        if from_ip and to_ip:
            rt = RouteStruct(agent_id=create_request.agent_id, routes=[
                IPv4Struct(address=from_ip['ip']),
                IPv4Struct(address=to_ip['ip'])
            ])
            task = db.task.create(status='FINISHED', params={})
            db.route.create(route=rt, task_id=task.id)
            return Response(status=201)
        else:
            return Response(body=f'Nu such ip: {create_request.from_ip} or {create_request.to_ip}')
        
    @BaseView.route("delete", "/create_edge")
    @project_require
    async def delete_edge(self, request: PMRequest):
        
        db = await get_db_by_session(request)
        try:
            delete_request = DeleteEdgeRequest.model_validate_json(await request.read())
        except ValidationError as e:
            return Response(body=e.json(), status=423)
        from_ip = db.ip.get_by_id(id=delete_request.from_ip)
        to_ip = db.ip.get_by_id(id=delete_request.to_ip)
        if from_ip and to_ip:
            ...
        else:
            return Response(body=f'Nu such ip: {delete_request.from_ip} or {delete_request.to_ip}')
