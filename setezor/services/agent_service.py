import logging
from typing import List
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.models import Agent, Object, MAC, IP, Network, ASN
from setezor.schemas.task import WebSocketMessage
from setezor.unit_of_work import UnitOfWork
from setezor.schemas.agent import AgentAdd, InterfaceOfAgent
from setezor.tools.ip_tools import get_network

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

class AgentService:
    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
            agents = await uow.agent.list(project_id=project_id)
            return agents
        
    @classmethod
    async def settings_page(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
            res = await uow.agent.settings_page(project_id=project_id)
            result = []
            for agent, parent_agent in res:
                result.append({
                    "id":agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "color": agent.color,
                    "rest_url": agent.rest_url,
                    "parent_agent_id": parent_agent.id if parent_agent else None,
                    "parent_agent_name": parent_agent.name if parent_agent else '',
                    "secret_key": agent.secret_key
                })
            logger.critical(f"List {len(result)} object of model {uow.agent.model}")
            return result
        
    @classmethod
    async def create(cls, uow: UnitOfWork, project_id: str, agent: AgentAdd) -> Agent:
        async with uow:
            new_obj_model = Object(project_id=project_id)
            new_obj = await uow.object.add(new_obj_model.model_dump())
            await uow.commit()

            new_agent_model = Agent(
                object_id=new_obj.id
            )

            new_agent_model.name = agent.name
            new_agent_model.description = agent.description
            new_agent_model.color = agent.color
            new_agent_model.rest_url = agent.rest_url
            new_agent_model.parent_agent_id = agent.parent_agent_id
            new_agent_model.project_id = project_id
            new_agent_model.secret_key = agent.secret_key

            new_agent = await uow.agent.add(new_agent_model.model_dump())
            await uow.commit()
            await uow.object.edit_one(new_obj.id, {"agent_id" : new_agent.id})
            await uow.commit()
         
            return new_agent
        
    @classmethod
    async def get_interfaces(cls, uow: UnitOfWork, project_id:str, id: int):
        async with uow:
            agent = await uow.agent.find_one(id=id, project_id=project_id)
            macs = await uow.mac.get_interfaces(object_id=agent.object_id)
            return macs
    
    @classmethod
    async def update_agent_color(cls, uow: UnitOfWork, project_id: str, agent_id:int, color: str):
        async with uow:
            agent_in_db = await uow.agent.find_one(id=agent_id, project_id=project_id)
            if not agent_in_db:
                return None
            agent = await uow.agent.edit_one(id = agent_id, data={"color" : color})
            await uow.commit()
            return color
        
    @classmethod
    async def save_interfaces(cls, uow: UnitOfWork, id: int, project_id: str, interfaces: List[InterfaceOfAgent]):
        async with uow:
            agent = await uow.agent.find_one(id=id)
            macs = await uow.mac.get_interfaces(object_id=agent.object_id)
            hashMap = set()
            for mac in macs:
                hashMap.add((mac.mac, mac.ip))
            for interface in interfaces:
                if (interface.mac, interface.ip) in hashMap: continue
                new_asn = ASN(project_id=project_id)
                start_ip, broadcast = get_network(ip=interface.ip, mask=24)
                new_network = Network(start_ip=start_ip, mask=24, project_id=project_id, asn=new_asn)

                new_mac = MAC(mac=interface.mac, name=interface.name, object_id=agent.object_id, project_id=project_id)
                new_ip = IP(ip=interface.ip, network=new_network, mac=new_mac, project_id=project_id)
                uow.session.add(new_ip)
            await uow.commit()
            # scans = await uow.scan.filter(project_id=project_id)
            # if not scans:
            #     first_scan = Scan(name="First scan", description="Initial scan after creating agents interfaces", project_id=project_id)
            #     await uow.scan.add(first_scan.model_dump())
            #     await uow.commit()
            message = WebSocketMessage(title="Info", text=f"Saved interfaces for {agent.name}",type="info")
            await WS_MANAGER.send_message(project_id=project_id, message=message) 
        return True
