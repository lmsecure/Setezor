
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from setezor.dependencies.project import get_current_project, get_current_scan_id, get_user_id, role_required
from setezor.managers.auth_manager import AuthManager
from setezor.models.scan import Scan
from setezor.schemas.scan import ScanCreateForm, ScanPickForm
from setezor.services.scan_service import ScanService
from setezor.schemas.roles import Roles

router = APIRouter(
    prefix="/scan",
    tags=["Scan"],
)

@router.get("")
async def get_scans(
    scan_service: Annotated[ScanService, Depends(ScanService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
)-> list[Scan]:
    return await scan_service.list(project_id=project_id)


@router.get("/current")
async def get_picked_scan(
    scan_service: Annotated[ScanService, Depends(ScanService.new_instance)],
    project_id: str = Depends(get_current_project),
    scan_id: str = Depends(get_current_scan_id),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> Scan:
    return await scan_service.get(id=scan_id, project_id=project_id)

@router.post("/set_current", status_code=200)
async def set_current(
    auth_manager: Annotated[AuthManager, Depends(AuthManager.new_instance)],
    scan: ScanPickForm,
    response: Response,
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> bool:
    token_pairs = await auth_manager.set_current_scan(project_id=project_id, user_id=user_id, scan_id = scan.scan_id)
    if not token_pairs:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    response.set_cookie(key="access_token", value=token_pairs.get("access_token"), secure=True, httponly=True)
    response.set_cookie(key="refresh_token", value=token_pairs.get("refresh_token"), secure=True, httponly=True)
    return True
