from typing import List, Dict

from fastapi import FastAPI, APIRouter, Depends, Query

from setezor.dependencies.project import get_current_project, get_user_id, role_required
from setezor.dependencies.uow_dependency import UOWDep
from setezor.models.d_object_type import ObjectType
from setezor.models.node_comment import NodeComment
from setezor.schemas.comment import NodeCommentForm
from setezor.services import NodeService, EdgeService, IPService
from setezor.schemas.ip import ChangeObjectType


router = APIRouter(
    prefix="/vis",
    tags=["Vis"],
)


@router.get("/edges")
async def list_edges(
    uow: UOWDep,
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner", "viewer"]))
) -> List:
    edges = await EdgeService.list(uow=uow, project_id=project_id, scans=scans)
    return edges


@router.get("/nodes")
async def list_nodes(
    uow: UOWDep,
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner", "viewer"]))
) -> List:
    nodes = await NodeService.list(uow=uow, project_id=project_id, scans=scans)
    return nodes


@router.get("/node_info/{ip_id}")
async def node_info(
    ip_id: str,
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner", "viewer"]))
) -> Dict:
    info = await NodeService.get_node_info(uow=uow, project_id=project_id, ip_id=ip_id)
    return info


@router.get("/comment/{ip_id}")
async def list_comments_for_node(
    ip_id: str,
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner", "viewer"]))
) -> list[dict]:
    comments = await NodeService.get_comments(uow=uow,
                                              ip_id=ip_id,
                                              project_id=project_id)
    return comments


@router.post("/comment")
async def add_comment_to_node(
    comment_form: NodeCommentForm,
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required(["owner", "viewer"]))
) -> NodeComment:
    new_comment = await NodeService.add_comment(uow=uow,
                                                user_id=user_id,
                                                project_id=project_id,
                                                comment_form=comment_form)
    return new_comment


@router.put("/set_object_type")
async def set_object_type(
    uow: UOWDep,
    payload: ChangeObjectType,
    project_id: str = Depends(get_current_project),
) -> ObjectType:
    return await IPService.update_object_type(uow=uow, project_id=project_id,
                                              **payload.model_dump())
