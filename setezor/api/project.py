from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status, Response, \
    UploadFile, File
from fastapi.responses import Response

from fastapi.responses import StreamingResponse
from setezor.dependencies.project import role_required, check_role
from setezor.managers import ProjectManager
from setezor.managers.auth_manager import AuthManager
from setezor.schemas.invite_link import InviteLinkCounter
from setezor.schemas.project import EnterTokenForm, ProjectCreateForm, ProjectPickForm, SearchVulnsSetTokenForm
from setezor.models import Project
from setezor.dependencies import get_current_project_for_ws, get_user_id, get_current_project
from setezor.managers import WS_MANAGER
from setezor.schemas.roles import Roles
from setezor.services.invite_link_service import InviteLinkService
from setezor.services.project_service import ProjectService
from setezor.services.scan_service import ScanService
from setezor.tools.websocket_manager import WS_USER_MANAGER

router = APIRouter(
    prefix="/project",
    tags=["Project"],
)


@router.post("", status_code=201)
async def create_project(
    form: ProjectCreateForm,
    project_manager: Annotated[ProjectManager, Depends(ProjectManager.new_instance)],
    scan_service: Annotated[ScanService, Depends(ScanService.new_instance)],
    auth_manager: Annotated[AuthManager, Depends(AuthManager.new_instance)],
    response: Response,
    user_id: str = Depends(get_user_id)
) -> Project:
    new_project = await project_manager.create_project(new_project_form=form,
                                                       owner_id=user_id)
    last_scan = await scan_service.get_latest(project_id=new_project.id)
    token_pairs = await auth_manager.set_current_scan(project_id=new_project.id,
                                                      user_id=user_id,
                                                      scan_id=last_scan.id)
    if not token_pairs:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    response.set_cookie(key="access_token",
                        value=token_pairs.get("access_token"),
                        secure=True,
                        httponly=True)
    response.set_cookie(key="refresh_token",
                        value=token_pairs.get("refresh_token"),
                        secure=True,
                        httponly=True)
    return new_project


@router.post("/set_current", status_code=200)
async def set_current(
    project: ProjectPickForm,
    response: Response,
    scan_service: Annotated[ScanService, Depends(ScanService.new_instance)],
    auth_manager: Annotated[AuthManager, Depends(AuthManager.new_instance)],
    user_id: str = Depends(get_user_id)
) -> bool:
    last_scan = await scan_service.get_latest(project_id=project.project_id)
    token_pairs = await auth_manager.set_current_scan(project_id=project.project_id,
                                                      user_id=user_id,
                                                      scan_id=last_scan.id)
    if not token_pairs:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    response.set_cookie(key="access_token",
                        value=token_pairs.get("access_token"),
                        secure=True,
                        httponly=True)
    response.set_cookie(key="refresh_token",
                        value=token_pairs.get("refresh_token"),
                        secure=True,
                        httponly=True)
    return True


@router.get("/{project_id}/export", status_code=200)
async def export_project_by_id(
    project_manager: Annotated[ProjectManager, Depends(ProjectManager.new_instance)],
    project_id: str,
    user_id: str = Depends(get_user_id),
) -> StreamingResponse:
    await check_role([Roles.owner], project_id, user_id)
    project = await project_manager.export_project(project_id, user_id)
    return StreamingResponse(
        project.data,
        media_type='application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename="{project.name}.zip"'}
    )


imported_projects = set()
@router.post("/import")
async def import_project(
    project_manager: Annotated[ProjectManager, Depends(ProjectManager.new_instance)],
    zip_file: UploadFile = File(...),
    user_id: str = Depends(get_user_id)
):
    await project_manager.import_project(user_id, zip_file, imported_projects)
    return Response(status_code=201)


@router.delete("/{project_id}", status_code=204)
async def delete_project_by_id(
    project_service: Annotated[ProjectService, Depends(ProjectService.new_instance)],
    project_id: str,
    user_id: str = Depends(get_user_id)
):
    return await project_service.delete_by_id(user_id=user_id,
                                              project_id=project_id)


@router.websocket("/ws")
async def websocket_handler(
    websocket: WebSocket,
    project_id: str = Depends(get_current_project_for_ws)
):
    await WS_MANAGER.connect(entity_id=project_id, websocket=websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        WS_MANAGER.disconnect(entity_id=project_id, websocket=websocket)


@router.websocket("/ws/users/{user_id}")
async def websocket_user_handler(
    websocket: WebSocket,
    user_id: str
):
    await WS_USER_MANAGER.connect(entity_id=user_id, websocket=websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        WS_USER_MANAGER.disconnect(entity_id=user_id, websocket=websocket)


@router.put("/search_vulns_token")
async def set_search_vulns_token(
    project_service: Annotated[ProjectService, Depends(ProjectService.new_instance)],
    token_form: SearchVulnsSetTokenForm,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner]))
):
    return await project_service.set_search_vulns_token(project_id=project_id,
                                                        token_form=token_form)


@router.post("/generate_invite_link")
async def generate_invite_link(
    invite_link_service: Annotated[InviteLinkService, Depends(InviteLinkService.new_instance)],
    generate_link_form: InviteLinkCounter,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner]))
):
    payload = {
        "project_id": project_id,
        "event": "enter"
    }
    return await invite_link_service.create_token(count_of_entries=generate_link_form.count,
                                                  payload=payload)


@router.post("/enter_by_token")
async def enter_by_invite_token(
    project_manager: Annotated[ProjectManager, Depends(ProjectManager.new_instance)],
    scan_service: Annotated[ScanService, Depends(ScanService.new_instance)],
    auth_manager: Annotated[AuthManager, Depends(AuthManager.new_instance)],
    enter_token_form: EnterTokenForm,
    response: Response,
    user_id: str = Depends(get_user_id),
):
    project_id = await project_manager.connect_new_user_to_project(user_id=user_id,
                                                                   enter_token_form=enter_token_form)
    last_scan = await scan_service.get_latest(project_id=project_id)
    token_pairs = await auth_manager.set_current_scan(project_id=project_id,
                                                      user_id=user_id,
                                                      scan_id=last_scan.id)
    if not token_pairs:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    response.set_cookie(key="access_token",
                        value=token_pairs.get("access_token"),
                        secure=True,
                        httponly=True)
    response.set_cookie(key="refresh_token",
                        value=token_pairs.get("refresh_token"),
                        secure=True,
                        httponly=True)
    return True
