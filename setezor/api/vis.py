from typing import List, Dict

from fastapi import FastAPI, APIRouter, Depends, Query

from setezor.dependencies.project import get_current_project, role_required
from setezor.dependencies.uow_dependency import UOWDep
from setezor.services import NodeService, EdgeService




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