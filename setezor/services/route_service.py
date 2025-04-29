from typing import List

from fastapi import HTTPException
from setezor.models.node_comment import NodeComment
from setezor.schemas.comment import NodeCommentForm
from setezor.unit_of_work import UnitOfWork
from setezor.interfaces.service import IService
from setezor.schemas.roles import Roles


class NodeService(IService):

    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str, scans: list[str]):
        async with uow:
            if (not scans) and (last_scan := await uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            vis_nodes_and_interfaces = await uow.ip.vis_nodes_and_interfaces(project_id=project_id, scans=scans)
            agents = await uow.agent_in_project.for_map(project_id=project_id)
            nodes = await uow.ip.get_nodes(project_id=project_id, scans=scans)
            server_agent = await uow.agent.find_one(name="Server", secret_key="")
            server_agent_in_project = await uow.agent_in_project.find_one(agent_id=server_agent.id, project_id=project_id)

        agents_ips = {}
        for row in vis_nodes_and_interfaces:
            if not agents_ips.get(row.ip_id):
                agents_ips[row.ip_id] = {"agents": set()}
                if row.agent_id:
                    agents_ips[row.ip_id].update(
                        {"agents": {row.agent_id}})
            else:
                if row.agent_id:
                    agents_ips[row.ip_id]["agents"].add(row.agent_id)

        result = []
        for agent in agents:
            result.append({
                "id": agent.id,
                "mac_address": "",
                "address": "",
                "agents": [agent.id],
                "agent": agent.id,
                "parent_agent_id": True if agent.id != server_agent_in_project.id else None,
                "group": "agents_group",
                "value": 1,
                "shape": "dot",
                "is_server": agent.rest_url and not agent.secret_key,
                "label": agent.name
            })
        for node in nodes:
            result.append({
                "id": node.id,
                "mac_address": node.mac,
                "address": node.ip,
                "agents": list(agents_ips[node.id]["agents"]) if node.id in agents_ips else [server_agent_in_project.id],
                "agent": None,
                "object_type": node.name,
                "group": f"{node.start_ip}/{node.mask}",
                "value": 1,
                "shape": "dot",
                "label": node.ip
            })
        return result

    @classmethod
    async def get_comments(cls, uow: UnitOfWork,
                           ip_id: str, project_id: str, user_id: str) -> List[dict]:
        async with uow:
            role = await uow.user_project.get_role_in_project(project_id=project_id, user_id=user_id)
            raw_comments = await uow.node_comment.for_node(ip_id=ip_id,
                                                           project_id=project_id,
                                                           hide_deleted=role!=Roles.owner)
        raw_comments = list(raw_comments)
        comments = {}
        for comment, user_login in raw_comments:
            if not comment.parent_comment_id:
                comments[comment.id] = {**comment.model_dump(), "login": user_login, "child_comments": []}
        for comment, user_login in raw_comments:
            if comment.parent_comment_id:
                comments[comment.parent_comment_id]["child_comments"].append({**comment.model_dump(), "login": user_login})
        return comments.values()

    @classmethod
    async def add_comment(cls, uow: UnitOfWork,
                          project_id: str,
                          user_id: str,
                          comment_form: NodeCommentForm):
        async with uow:
            new_comment_form = NodeComment(project_id=project_id,
                                           user_id=user_id,
                                           **comment_form.model_dump())
            new_comment = uow.node_comment.add(
                data=new_comment_form.model_dump())
            await uow.commit()
            return new_comment


    @classmethod
    async def update_comment(cls, uow: UnitOfWork,
                             project_id: str,
                             user_id: str,
                             comment_id: str,
                             comment_text: str):
        async with uow:
            comment = await uow.node_comment.find_one(id=comment_id, project_id=project_id)
            role = await uow.user_project.get_role_in_project(project_id=project_id, user_id=user_id)
            if comment.user_id == user_id or role == Roles.owner:
                await uow.node_comment.edit_one(id=comment_id, data={"text" : comment_text})
                await uow.commit()
                return await uow.node_comment.find_one(id=comment_id)
            raise HTTPException(status_code=403, detail="You can't edit this comment")


    @classmethod
    async def delete_comment(cls, uow: UnitOfWork, project_id: str, user_id: str, comment_id: str):
        async with uow:
            comment = await uow.node_comment.find_one(id=comment_id, project_id=project_id)
            role = await uow.user_project.get_role_in_project(project_id=project_id, user_id=user_id)
            if comment.user_id == user_id or role == Roles.owner:
                if not comment.parent_comment_id:
                    sub_comments = await uow.node_comment.filter(parent_comment_id=comment_id, project_id=project_id)
                    for sub_comment in sub_comments:
                        await uow.node_comment.delete(id=sub_comment.id)
                await uow.node_comment.delete(id=comment_id)
                await uow.commit()
                return
        raise HTTPException(status_code=403, detail="You can't delete this comment")


    @classmethod
    async def get_node_info(cls, uow: UnitOfWork, project_id: str, ip_id: int):
        async with uow:
            ip_obj, mac_obj, network_obj = await uow.ip.get_node_info(project_id=project_id, ip_id=ip_id)
            domain_objs = await uow.domain.get_node_info(project_id=project_id, ip_id=ip_id)
            port_objs = await uow.port.get_node_info(project_id=project_id, ip_id=ip_id)
        domain_list = [item.domain for item in domain_objs if item.domain]
        port_list = []
        for port, soft in port_objs:
            port_list.append({
                "port_id": port.id,
                "port": port.port,
                "protocol": port.protocol,
                "state": port.state,
                "software": soft.product if soft else "",
            })
        result = {
            "ip": ip_obj.ip,
            "mac": mac_obj.mac,
            "network": f"{network_obj.start_ip}/{network_obj.mask}",
            "domain": '; '.join(domain_list),
            "ports": port_list
        }
        return result


class EdgeService(IService):

    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str, scans: list[str], agents_parents: dict):
        async with uow:
            if (not scans) and (last_scan := await uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)

            agents_in_project = await uow.agent_in_project.filter(project_id=project_id)
            edges = []
            for agent_in_project in agents_in_project:
                for parent in agents_parents.get(agent_in_project.agent_id, []):
                    edges.append({"from": parent["parent_agent_id_in_project"], "to": agent_in_project.id})

            vis_edge_agent_to_interface = await uow.route_list.vis_edge_agent_to_interface(project_id=project_id)
            edges.extend([{"from": row[0], "to": row[1], "length": 100}
                         for row in vis_edge_agent_to_interface])

            vis_edge_node_to_node = await uow.route_list.vis_edge_node_to_node(project_id=project_id, scans=scans)
            seen = set()
            for row in vis_edge_node_to_node:
                key = (row.ip_id_from, row.ip_id_to)
                if key not in seen:
                    edges.append({"from": row.ip_id_from, "to": row.ip_id_to})
                    seen.add(key)

            return edges
