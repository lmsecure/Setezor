from typing import List


from setezor.models.node_comment import NodeComment
from setezor.schemas.comment import NodeCommentForm
from setezor.unit_of_work import UnitOfWork
from setezor.interfaces.service import IService


class NodeService(IService):

    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str, scans: list[str]):
        async with uow:
            if (not scans) and (last_scan := await uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)

            agents_ips = {}

            vis_nodes_and_interfaces = await uow.ip.vis_nodes_and_interfaces(project_id=project_id, scans=scans)
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

            agents = await uow.agent.list(project_id=project_id)
            for agent in agents:
                result.append({
                    "id": agent.id,
                    "mac_address": "",
                    "address": "",
                    "agents": [agent.id],
                    "agent": agent.id,
                    "parent_agent_id": agent.parent_agent_id,
                    "group": "agents_group",
                    "value": 1,
                    "shape": "dot",
                    "label": agent.name
                })


            nodes_with_comment = await uow.node_comment.list_nodes_with_comment(project_id=project_id)
            nodes_with_comment_set = {t for t in nodes_with_comment}
            nodes = await uow.ip.get_nodes(project_id=project_id, scans=scans)
            for node in nodes:
                result.append({
                    "id": node.id,
                    "mac_address": node.mac,
                    "address": node.ip,
                    "agents": list(agents_ips[node.id]["agents"]) if node.id in agents_ips else [],
                    "agent": None,
                    "object_type": node.name,
                    "group": f"{node.start_ip}/{node.mask}",
                    "value": 1,
                    "shape": "dot",
                    "label": node.ip,
                    "has_comments": node.id in nodes_with_comment_set
                })

            return result

    @classmethod
    async def get_comments(cls, uow: UnitOfWork,
                           ip_id: str, project_id: str) -> List[dict]:
        async with uow:
            raw_comments = await uow.node_comment.for_node(ip_id=ip_id,
                                                           project_id=project_id)
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
    async def get_node_info(cls, uow: UnitOfWork, project_id: str, ip_id: int):
        async with uow:
            ip_obj, mac_obj, network_obj, port_soft = await uow.ip.get_node_info(project_id=project_id, ip_id=ip_id)
            ports_list = []
            for port, soft in port_soft:
                ports_list.append({
                    "port": port.port,
                    "protocol": port.protocol,
                    "state": port.state,
                    "software": soft.product,
                })
            result = {
                "ip": ip_obj.ip,
                "mac": mac_obj.mac,
                "network": f"{network_obj.start_ip}/{network_obj.mask}",
                "ports": ports_list
            }
            return result


class EdgeService(IService):

    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str, scans: list[str]):
        async with uow:
            if (not scans) and (last_scan := await uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)

            vis_edge_agent_to_agent = await uow.route_list.vis_edge_agent_to_agent(project_id=project_id)
            edges: list = [{"from": row[0], "to": row[1]}
                           for row in vis_edge_agent_to_agent]

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
