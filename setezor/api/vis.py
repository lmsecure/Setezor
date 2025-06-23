from typing import Annotated, List, Dict

from fastapi import APIRouter, Depends, Query

from setezor.dependencies.project import get_current_project, get_user_id, role_required
from setezor.models.d_object_type import ObjectType
from setezor.models.node_comment import NodeComment
from setezor.schemas.comment import NodeCommentForm
from setezor.schemas.credentials import CredentialsForm
from setezor.services import NodeService, EdgeService, IPService, AgentInProjectService, CredentialsService, NetworkSpeedTestService
from setezor.schemas.ip import ChangeObjectType
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/vis",
    tags=["Vis"],
)


@router.get("/edges")
async def list_edges(
    agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
    edge_service: Annotated[EdgeService, Depends(EdgeService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(
        [Roles.owner, Roles.executor, Roles.viewer]))
) -> List:
    agents_parents = await agent_in_project_service.get_id_and_names_from_parents(project_id=project_id)
    edges = await edge_service.list(project_id=project_id, scans=scans, agents_parents=agents_parents)
    return edges


@router.get("/nodes")
async def list_nodes(
    node_service: Annotated[NodeService, Depends(NodeService.new_instance)],
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(
        [Roles.owner, Roles.executor, Roles.viewer]))
) -> List:
    nodes = await node_service.list(project_id=project_id, scans=scans)
    return nodes


@router.get("/node_info/{ip_id}")
async def node_info(
    ip_id: str,
    node_service: Annotated[NodeService, Depends(NodeService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(
        [Roles.owner, Roles.executor, Roles.viewer]))
) -> Dict:
    info = await node_service.get_node_info(project_id=project_id, ip_id=ip_id)
    return info


@router.get("/comment/{ip_id}")
async def list_comments_for_node(
    ip_id: str,
    node_service: Annotated[NodeService, Depends(NodeService.new_instance)],
    user_id: str = Depends(get_user_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(
        [Roles.owner, Roles.executor, Roles.viewer]))
) -> list[dict]:
    comments = await node_service.get_comments(ip_id=ip_id,
                                               project_id=project_id,
                                               user_id=user_id)
    return comments


@router.post("/comment")
async def add_comment_to_node(
    comment_form: NodeCommentForm,
    node_service: Annotated[NodeService, Depends(NodeService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required(
        [Roles.owner, Roles.executor, Roles.viewer]))
) -> NodeComment:
    new_comment = await node_service.add_comment(user_id=user_id,
                                                 project_id=project_id,
                                                 comment_form=comment_form)
    return new_comment


@router.put("/comment/{comment_id}")
async def update_comment(
    comment_id: str,
    comment_text: str,
    node_service: Annotated[NodeService, Depends(NodeService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required(
        [Roles.owner, Roles.executor, Roles.viewer]))
) -> NodeComment:
    new_comment = await node_service.update_comment(user_id=user_id,
                                                    project_id=project_id,
                                                    comment_id=comment_id,
                                                    comment_text=comment_text)
    return new_comment


@router.delete("/comment/{comment_id}")
async def delete_comment(
    comment_id: str,
    node_service: Annotated[NodeService, Depends(NodeService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required(
        [Roles.owner, Roles.executor, Roles.viewer]))
) -> None:
    await node_service.delete_comment(project_id=project_id, user_id=user_id, comment_id=comment_id)


@router.get("/credentials/{ip_id}")
async def get_credentials_for_node(
    ip_id: str,
    credentials_service: Annotated[CredentialsService, Depends(CredentialsService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id)
) -> list[Dict]:
    result = await credentials_service.get_credentials_for_node(ip_id=ip_id, project_id=project_id)
    return result


@router.get("/speed_test_result")
async def get_speed_test_result(
    ip_id_from: str,
    ip_id_to: str,
    network_speed_test_service: Annotated[NetworkSpeedTestService, Depends(NetworkSpeedTestService.new_instance)],
    project_id: str = Depends(get_current_project),
) -> list[dict]:
    result = await network_speed_test_service.get_result(project_id=project_id, ip_id_from=ip_id_from, ip_id_to=ip_id_to)
    return result


@router.post("/credentials")
async def add_credentials_to_node(
    payload: CredentialsForm,
    credentials_service: Annotated[CredentialsService, Depends(CredentialsService.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id)
) -> dict:
    new_cred_obj = await credentials_service.add_credentials(project_id=project_id, data=payload.model_dump())
    return new_cred_obj


@router.put("/set_object_type")
async def set_object_type(
    ip_service: Annotated[IPService, Depends(IPService.new_instance)],
    payload: ChangeObjectType,
    project_id: str = Depends(get_current_project),
) -> ObjectType:
    return await ip_service.update_object_type(project_id=project_id,
                                               **payload.model_dump())
