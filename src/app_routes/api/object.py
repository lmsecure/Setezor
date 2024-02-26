from typing import TypedDict

from aiohttp.web import Request, Response, json_response

from app_routes.session import project_require, get_db_by_session
from app_routes.api.base_web_view import BaseView
from modules.application import PMRequest
from database.models import IP

class NodeCreateJsonResponse(TypedDict):
    
    id: int
    label: int
    group: str
    mac: str | None
    os: str | None
    vendor: str | None
    domain: str | None

class ObjectView(BaseView):
    endpoint = '/object'
    queries_path = 'object'
    
    @BaseView.route('PUT', '/')
    async def update(self, request: PMRequest):
        db_entity = await self.get_db_queries(request=request)
        params = await request.json()
        db_entity.update_by_ip_id(ip_id=params.get('ip_id'), to_update=params.get('to_update'))
        return json_response(status=200, data={'status': 'ok'})
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: PMRequest):
        db = await get_db_by_session(request=request)
        objects = db.object.get_all()
        return json_response(status=200, data=[{'value': i.get('id'), 'label': i.get('object_type')} for i in objects])
    
    @BaseView.route('PUT', '/create_object')
    @project_require
    async def create_object(self, request: PMRequest):
        
        """Создает цепочку ip, mac, object"""
        
        db = await get_db_by_session(request)
        data: NodeCreateJsonResponse = await request.json()
        ip = data.get('label')
        os = data.get('os')
        mac = data.get('mac')
        domain = data.get('domain')
        vendor = data.get('vendor')
        ip_obj = db.ip.get_by_ip(ip=ip)
        if ip_obj:
            return Response(status=404, reason=f'Ip {ip} exists')
        
        if mac:
            mac_object = db.mac.get_by_mac(mac=mac)
            if mac_object:
                return Response(status=404, reason='На данный момент нельзя добавлять mac к существующему ip')
        ip_obj: IP = db.ip.create(ip=ip, mac=mac, domain_name=domain)
        if vendor:
            db.mac.add_vendor(mac=ip_obj._mac, vendor=vendor)
            
        if os:
            db.object.add_os(obj=ip_obj._mac._obj, os=os)
            
        return json_response({'object_id': ip_obj._mac._obj.id})
    
    @BaseView.route('PUT', '/update_object')
    @project_require
    async def update_object(self, request: PMRequest):
        
        """Обновляет ноду на l3 карте"""
        
        db = await get_db_by_session(request)
        data: NodeCreateJsonResponse = await request.json()
        ip = data.get('label')
        os = data.get('os')
        mac = data.get('mac')
        domain = data.get('domain')
        vendor = data.get('vendor')
        ip_obj = db.ip.get_by_ip(ip=ip)
        if not ip_obj:
            return Response(status=404, reason=f'Ip {ip} doesn\'t exists')
        ip_obj = db.ip.edit_ip(ip=ip, domain=domain, os=os, mac=mac, vendor=vendor)
            
        return json_response({'object_id': ip_obj._mac._obj.id})
    
    @BaseView.route('DELETE', '/delete_object')
    @project_require
    async def delete_object(self, request: PMRequest):
        
        db = await get_db_by_session(request)
        ip = await request.text()
        ip_obj = db.ip.get_by_ip(ip=ip)
        db.object.delete_by_id(id=ip_obj._mac._obj.id)
        return Response()