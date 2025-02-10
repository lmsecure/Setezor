from typing import List
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.models import Agent, Object, MAC, IP, Network, ASN
from setezor.models.base import generate_unique_id
from setezor.schemas.task import WebSocketMessage
from setezor.unit_of_work import UnitOfWork
from setezor.schemas.agent import AgentAdd, InterfaceOfAgent
from setezor.tools.ip_tools import get_network

class AgentService:
    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
            agents = await uow.agent.list(project_id=project_id)
            return agents
        
    @classmethod
    async def get(cls, uow: UnitOfWork, id: str, project_id: str) -> Agent:
        async with uow:
            return await uow.agent.find_one(id=id, project_id=project_id)
            
    @classmethod
    async def get_by_id(cls, uow: UnitOfWork, id: str) -> Agent:
        async with uow:
            return await uow.agent.find_one(id=id)

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
            return result
        
    @classmethod
    async def create(cls, uow: UnitOfWork, project_id: str, agent: AgentAdd) -> Agent:
        async with uow:
            obj_id, ag_id = generate_unique_id(), generate_unique_id()
            new_obj_model = Object(id=obj_id,
                                   agent_id=ag_id,
                                   project_id=project_id)
            
            new_obj = uow.object.add(new_obj_model.model_dump())

            new_agent_model = Agent(
                id=ag_id,
                object_id=new_obj.id,
                name = agent.name,
                description = agent.description,
                color = agent.color,
                rest_url = agent.rest_url,
                parent_agent_id = agent.parent_agent_id,
                project_id = project_id,
                secret_key = agent.secret_key,
            )
            new_agent = uow.agent.add(new_agent_model.model_dump())
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
            agent = await uow.agent.edit_one(id=agent_id, data={"color" : color})
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
                new_asn = ASN(id=generate_unique_id(), 
                              project_id=project_id)
                uow.asn.add(new_asn.model_dump())

                start_ip, broadcast = get_network(ip=interface.ip, mask=24)
                new_network = Network(id=generate_unique_id(), 
                                      start_ip=start_ip, 
                                      mask=24, 
                                      project_id=project_id, 
                                      asn_id=new_asn.id)
                uow.network.add(new_network.model_dump())

                new_mac = MAC(id=generate_unique_id(), 
                              mac=interface.mac,
                              name=interface.name,
                              object_id=agent.object_id,
                              project_id=project_id)
                uow.mac.add(new_mac.model_dump())

                new_ip = IP(ip=interface.ip, 
                            network_id=new_network.id, 
                            mac_id=new_mac.id, 
                            project_id=project_id)
                uow.ip.add(new_ip.model_dump())
            await uow.commit()
            # scans = await uow.scan.filter(project_id=project_id)
            # if not scans:
            #     first_scan = Scan(name="First scan", description="Initial scan after creating agents interfaces", project_id=project_id)
            #     await uow.scan.add(first_scan.model_dump())
            #     await uow.commit()
            message = WebSocketMessage(title="Info", text=f"Saved interfaces for {agent.name}",type="info")
            await WS_MANAGER.send_message(project_id=project_id, message=message) 
        return True


    @classmethod
    async def get_agents_chain(cls, uow: UnitOfWork, agent_id: str, project_id: str):
        agents_chain_urls = []
        async with uow:
            while True:
                agent = await uow.agent.find_one(id=agent_id, project_id=project_id)
                if not agent.parent_agent_id: break
                agent_id = agent.parent_agent_id
                agents_chain_urls.append(agent)
        return agents_chain_urls
    
    @classmethod
    async def set_key(cls, uow: UnitOfWork, id: str, key: str):
        async with uow:
            await uow.agent.edit_one(id=id, data={"secret_key": key})
            await uow.commit()