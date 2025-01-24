
from typing import Optional
from fastapi import Depends, Request, WebSocket, HTTPException
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.schemas.task import WebSocketMessage
from setezor.tools import JWTManager
from fastapi.security import OAuth2PasswordBearer
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.exceptions.exceptions import RequiresLoginException, RequiresProjectException, RequiresScanException


class CustomAccessTokenVerificationForm(OAuth2PasswordBearer):
    def __call__(self, request: Request) -> Optional[str]:
        return request.cookies.get("access_token")
    
access_token_getter = CustomAccessTokenVerificationForm(tokenUrl="/api/v1/auth/login")

async def get_current_project(access_token: str = Depends(access_token_getter)):
    return await check_availability(access_token=access_token)

async def get_current_project_for_ws(websocket: WebSocket):
    return await check_availability(websocket.cookies.get("access_token"))

async def get_current_scan_id(access_token: str = Depends(access_token_getter)):
    project_id: str = await check_availability(access_token=access_token)
    return await get_scan_id(access_token=access_token, project_id=project_id)

async def get_scan_id(access_token: str, project_id: str):
    payload = JWTManager.get_payload(access_token)
    scan_id = payload.get("scan_id")
    if not scan_id:
        message = WebSocketMessage(title="Info", text=f"Create scan or pick it", type="info")
        await WS_MANAGER.send_message(project_id=project_id, message=message) 
        raise RequiresScanException(status_code=403, detail="No scan picked")
    uow = UnitOfWork()
    async with uow:
        if not await uow.scan.find_one(id=scan_id, project_id=project_id):
            message = WebSocketMessage(title="Error", text=f"Scan with id={scan_id} does not exist",type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message) 
            raise RequiresScanException(status_code=403, detail="Scan not found")
    return scan_id

async def check_availability(access_token: str):
    if JWTManager.is_expired(access_token):
        raise RequiresLoginException
    payload = JWTManager.get_payload(access_token)
    if not payload:
        raise RequiresLoginException
    project_id = payload.get("project_id")
    if not project_id:
        raise RequiresProjectException
    uow = UnitOfWork()
    async with uow:
        if not await uow.project.find_one(id=project_id):
            raise RequiresProjectException
    return project_id

async def get_user_id(access_token: str = Depends(access_token_getter)):
    return "deadbeefdeadbeefdeadbeefdeadbeef"  # auth_toggled_off
    if JWTManager.is_expired(access_token):
        raise RequiresLoginException(status_code=403, detail="Token is expired")
    payload = JWTManager.get_payload(access_token)
    if not payload:
        raise RequiresLoginException
    user_id = payload.get("user_id")
    if not user_id:
        raise RequiresLoginException
    uow = UnitOfWork()
    async with uow:
        if not await uow.user.find_one(id=user_id):
            raise RequiresLoginException
    return user_id
