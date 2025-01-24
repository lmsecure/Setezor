from typing import List, Dict

from fastapi import FastAPI, APIRouter, Depends, Query

from setezor.dependencies.project import get_current_project
from setezor.api.dependencies import UOWDep
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
) -> List:
    edges = await EdgeService.list(uow=uow, project_id=project_id, scans=scans)
    return edges


@router.get("/nodes")
async def list_nodes(
    uow: UOWDep,
    scans: list[str] = Query([]),
    project_id: str = Depends(get_current_project),
) -> List:
    nodes = await NodeService.list(uow=uow, project_id=project_id, scans=scans)
    return nodes

@router.get("/node_info/{ip_id}")
async def node_info(
    ip_id: str,
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
) -> Dict:
    info = await NodeService.get_node_info(uow=uow, project_id=project_id, ip_id=ip_id)
    return info