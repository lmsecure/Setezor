
from fastapi import APIRouter, Depends
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project, get_current_scan_id
from setezor.models.scan import Scan
from setezor.services.scan_service import ScanService

router = APIRouter(
    prefix="/scan",
    tags=["Scan"],
)

@router.get("")
async def get_scans(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
)-> list[Scan]:
    return await ScanService.list(uow=uow, project_id=project_id)


@router.get("/current")
async def get_picked_scan(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    scan_id: str = Depends(get_current_scan_id),
) -> Scan:
    return await ScanService.get(uow=uow, id=scan_id)