
from typing import Annotated, Optional
from fastapi import Depends, Request, WebSocket, HTTPException
from setezor.db.uow_dependency import get_uow
from setezor.managers.user_manager import UserManager
from setezor.tools.websocket_manager import WS_MANAGER
from setezor.schemas.task import WebSocketMessage
from setezor.tools import JWT_Tool
from fastapi.security import OAuth2PasswordBearer
from setezor.exceptions.exceptions import RequiresLoginException, RequiresProjectException, RequiresScanException


class CustomAccessTokenVerificationForm(OAuth2PasswordBearer):
    def __call__(self, request: Request) -> Optional[str]:
        return request.cookies.get("access_token")


access_token_getter = CustomAccessTokenVerificationForm(
    tokenUrl="/api/v1/auth/login")


async def get_current_project(access_token: str = Depends(access_token_getter)):
    return await check_availability(access_token=access_token)


async def get_current_project_for_ws(websocket: WebSocket):
    return await check_availability(websocket.cookies.get("access_token"))


async def get_current_scan_id(access_token: str = Depends(access_token_getter)):
    project_id: str = await check_availability(access_token=access_token)
    return await get_scan_id(access_token=access_token, project_id=project_id)


async def get_scan_id(access_token: str, project_id: str):
    payload = JWT_Tool.get_payload(access_token)
    scan_id = payload.get("scan_id")
    user_id = payload.get("user_id")
    if not scan_id:
        message = WebSocketMessage(title="Info", text=f"Create scan or pick it",
                                   type="info", user_id=user_id, command="notify_user")
        await WS_MANAGER.send_message(project_id=project_id, message=message)
        raise RequiresScanException(status_code=404, detail="No scan picked")
    uow = get_uow()
    async with uow:
        if not await uow.scan.find_one(id=scan_id, project_id=project_id):
            message = WebSocketMessage(
                title="Error", text=f"Scan with id={scan_id} does not exist", type="error", user_id=user_id, command="notify_user")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise RequiresScanException(
                status_code=404, detail="Scan not found")
    return scan_id


async def check_availability(access_token: str):
    if JWT_Tool.is_expired(access_token):
        raise RequiresLoginException(
            status_code=403, detail="Not authenticated")
    payload = JWT_Tool.get_payload(access_token)
    if not payload:
        raise RequiresLoginException(
            status_code=403, detail="No token provided")
    project_id = payload.get("project_id")
    if not project_id:
        raise RequiresProjectException(
            status_code=403, detail="Project is not picked")
    uow = get_uow()
    async with uow:
        if await uow.project.find_one(id=project_id):
            return project_id
    raise RequiresProjectException(status_code=403, detail="Project not found")


async def get_user_id(access_token: str = Depends(access_token_getter)):
    if JWT_Tool.is_expired(access_token):
        raise RequiresLoginException(
            status_code=403, detail="Token is expired")
    payload = JWT_Tool.get_payload(access_token)
    if not payload:
        raise RequiresLoginException(
            status_code=403, detail="Token is expired")
    user_id = payload.get("user_id")
    if not user_id:
        raise RequiresLoginException(
            status_code=403, detail="Token is expired")
    uow = get_uow()
    async with uow:
        if await uow.user.find_one(id=user_id):
            return user_id
    raise RequiresLoginException(status_code=403, detail="Token is expired")


def role_required(required_roles: list[str]):
    async def role_checker(user_id: str = Depends(get_user_id),
                           project_id: str = Depends(get_current_project)):
        uow = get_uow()
        async with uow:
            user_project = await uow.user_project.find_one(user_id=user_id, project_id=project_id)
            user_role_in_project = await uow.role.find_one(id=user_project.role_id)
        if not (user_role_in_project.name in required_roles):
            # message = WebSocketMessage(title="Error", text=f"Not enough permissions",type="error")
            # await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise HTTPException(
                status_code=403, detail="Недостаточно прав для выполнения данного действия")
        return True
    return role_checker


async def get_user_role_in_project(
    user_manager:  Annotated[UserManager, Depends(UserManager.new_instance)],
    project_id: str = Depends(get_current_project),
    user_id: str = Depends(get_user_id)
):
    return await user_manager.get_user_role(project_id=project_id, user_id=user_id)
