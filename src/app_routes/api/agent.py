from typing import Any, Coroutine
from aiohttp.web import Request, Response, json_response

import orjson
from pydantic import ValidationError, BaseModel, Field, AliasChoices

from app_routes.session import project_require, get_db_by_session, get_project
from app_routes.api.base_web_view import BaseView
from modules.application import PMRequest

from network_structures import AgentStruct, IPv4Struct

class EditRequest(BaseModel):
    id: int
    field: str
    value: Any
    
class RGB(BaseModel):
    red: int = Field(ge=0, le=255, validation_alias=AliasChoices('red', 'r'))
    green: int = Field(ge=0, le=255, validation_alias=AliasChoices('green', 'g'))
    blue: int = Field(ge=0, le=255, validation_alias=AliasChoices('blue', 'b'))

class AgentView(BaseView):
    endpoint = '/agent'
    queries_path = 'agent'
    
    @BaseView.route('post', '/create')
    @project_require
    async def create(self, request: PMRequest) -> Coroutine[Any, Any, Response]:
        body = await request.read()
        try:
            agent = AgentStruct.model_validate_json(body)
            agent.id = None
            db = await get_db_by_session(request)
            db.agent.create(agent=agent)
            return Response(status=201)
        except ValidationError as e:
            return Response(body=str(e), status=423)
        
    @BaseView.route('put', '/update')
    @project_require
    async def edit(self, request: PMRequest) -> Coroutine[Any, Any, Response]:
        body = await request.read()
        try:
            data = EditRequest.model_validate_json(body)
            db = await get_db_by_session(request)
            if data.field == 'color':
                try:
                    color = RGB.model_validate(data.value)
                    db.agent.update_by_id(id=data.id, to_update=color.model_dump(exclude={'id'}))
                    return Response(status=204)
                except ValidationError as e:
                    return Response(body=e.json(include_url=False), status=423)
            else:
                res = db.agent.update_by_id(id=data.id, to_update={data.field: data.value})
                if res:
                    return Response(status=204)
                else:
                    return Response(status=500, body='Error on updating value in database')
        except ValidationError as e:
            return Response(body=e.json(include_url=False), status=423)
        
    @BaseView.route('get', '/names')
    @project_require
    async def get_names(self, request: PMRequest):
    
        db = await get_db_by_session(request)
        res = db.agent.get_names()
        res = [{'id': i[0], 'name': i[1]} for i in res]
        res = orjson.dumps(res)
        return Response(body=res)
    
    @BaseView.route('get', '/get_default')
    @project_require
    async def get_default(self, request: PMRequest):
        project = await get_project(request)
        return Response(body=str(project.configs.variables.default_agent['id']))
    
    @BaseView.route('put', '/set_default')
    @project_require
    async def change_default_agent(self, request: PMRequest):
        agent_id = request.rel_url.query.get("agent_id")
        if not agent_id:
            return Response(body="You must specify agent_id", status=423)
        try:
            agent_id = int(agent_id)
        except Exception:
            return Response(body="Agent id must be int", status=423)
        
        db = await get_db_by_session(request)
        session = db.db.create_session()
        db_agent = db.agent.get_by_id(session=session, id=agent_id)
        if not db_agent:
            return Response(body=f"No such agent with id={agent_id}", status=404)
        project = await get_project(request)
        agent = AgentStruct(
            id=db_agent.id,
            name=db_agent.name,
            description=db_agent.description,
            red=db_agent.red,
            green=db_agent.green,
            blue=db_agent.blue,
            ip=db_agent.ip.ip
        )
        agent.ip = str(agent.ip.address)
        project.configs.variables.default_agent = agent.model_dump()
        project.configs.save_config_file()
        return Response()
        