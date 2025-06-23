import string
from typing import Annotated

from fastapi import Depends, HTTPException, status
from setezor.models.user import User
from setezor.schemas.auth import RegisterForm
from setezor.services.auth_log_service import Auth_Log_Service
from setezor.services.invite_link_service import InviteLinkService
from setezor.services.project_service import ProjectService
from setezor.services.user_project_service import UserProjectService
from setezor.services.user_service import UsersService
from setezor.tools.jwt import JWT_Tool
from setezor.tools.password import PasswordTool


class AuthManager:
    def __init__(self,
                 invite_link_service: InviteLinkService,
                 users_service: UsersService,
                 user_project_service: UserProjectService,
                 auth_log_service: Auth_Log_Service,
                 project_service: ProjectService,
                 ):
        self.__invite_link_service = invite_link_service
        self.__users_service = users_service
        self.__user_project_service = user_project_service
        self.__project_service = project_service
        self.__auth_log_service = auth_log_service

    async def login(self, username: str, password: str):
        await self.__auth_log_service.log_event(login=username, event="LOGIN ATTEMPT")
        if not (user_in_db := await self.__users_service.get_by_login(login=username)):
            await self.__auth_log_service.log_event(login=username, event="LOGIN DOES NOT EXIST")
            return None
        if not PasswordTool.verify_password(password, user_in_db.hashed_password):
            await self.__auth_log_service.log_event(login=username, event="INVALID PASSWORD")
            return None
        await self.__auth_log_service.log_event(login=username, event="SUCCESSFUL LOGIN")
        access_token = JWT_Tool.create_access_token(
            data={"user_id": user_in_db.id})
        refresh_token = JWT_Tool.create_refresh_token(
            data={"user_id": user_in_db.id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }

    async def set_current_project(self, project_id: str, user_id: str):
        user = await self.__users_service.get(id=user_id)
        await self.__auth_log_service.log_event(login=user.login, event=f"PROJECT PICK ATTEMPT {project_id}")
        if not (await self.__project_service.get_by_id(project_id=project_id)):
            await self.__auth_log_service.log_event(login=user.login, event=f"NONEXISTENT PROJECT {project_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Проект с ID={project_id} не существует")
        if not (await self.__user_project_service.get_user_project(project_id=project_id, user_id=user_id)):
            await self.__auth_log_service.log_event(login=user.login, event=f"UNAVAILABLE PROJECT {project_id} FOR USER")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Тебе сюда нельзя")
        await self.__auth_log_service.log_event(login=user.login, event=f"SUCCESSFUL PROJECT {project_id} PICK")
        access_token = JWT_Tool.create_access_token(
            data={"user_id": user_id, "project_id": project_id})
        refresh_token = JWT_Tool.create_refresh_token(
            data={"user_id": user_id, "project_id": project_id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }

    async def set_current_scan(self, project_id: str, user_id: str, scan_id: str):
        if not (await self.__project_service.get_by_id(project_id)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Проект с ID={project_id} не существует")
        if not (await self.__user_project_service.get_user_project(project_id=project_id, user_id=user_id)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Тебе сюда нельзя")
        access_token = JWT_Tool.create_access_token(
            data={"user_id": user_id, "project_id": project_id, "scan_id": scan_id})
        refresh_token = JWT_Tool.create_refresh_token(
            data={"user_id": user_id, "project_id": project_id, "scan_id": scan_id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }

    async def logout_from_project(self, access_token: str):
        access_token_payload = JWT_Tool.get_payload(access_token)
        user_id = access_token_payload.get("user_id")
        access_token = JWT_Tool.create_access_token(data={"user_id": user_id})
        refresh_token = JWT_Tool.create_refresh_token(
            data={"user_id": user_id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }

    async def generate_register_token(self, count_of_entries: int,
                                      user_id: str) -> dict:
        user = await self.__users_service.get(user_id=user_id)
        if not user.is_superuser:
            raise HTTPException(
                status_code=403, detail="You are not superuser")
        payload = {"event": "register"}
        return await self.__invite_link_service.create_token(count_of_entries=count_of_entries, payload=payload)

    async def register_by_invite_token(self, open_reg: bool, register_form: RegisterForm):
        if register_form.password != register_form.password_confirmation:
            raise HTTPException(
                status_code=400, detail="Password and password confirmation mismatch")
        if not open_reg:
            invite_link = await self.__invite_link_service.get_by_hash(
                token_hash=register_form.invite_token)
            if not invite_link:
                raise HTTPException(status_code=400, detail="Token not found")
            token_payload = JWT_Tool.get_payload(invite_link.token)
            if not token_payload:
                raise HTTPException(status_code=403, detail="Token is expired")
            if not invite_link.count_of_entries:
                raise HTTPException(status_code=403, detail="Invalid token")
        if not all([c in string.ascii_letters + string.digits for c in register_form.login]):
            raise HTTPException(
                status_code=400, detail="Username can only contain letters and digits")
        if await self.__users_service.get_by_login(login=register_form.login):
            raise HTTPException(
                status_code=400, detail="Username is already taken")

        if not open_reg:
            event = token_payload.get("event")
            if event == "register":
                await self.__invite_link_service.change_count_of_entries(token_id=invite_link.id,
                                                                         new_count_of_entries=invite_link.count_of_entries-1)

        hashed_password = PasswordTool.hash(register_form.password)
        new_user_model = User(
            login=register_form.login,
            hashed_password=hashed_password
        )
        await self.__users_service.create(new_user_model)
        return True

    @classmethod
    def new_instance(
        cls,
        invite_link_service: Annotated[InviteLinkService, Depends(InviteLinkService.new_instance)],
        users_service:  Annotated[UsersService, Depends(UsersService.new_instance)],
        user_project_service:  Annotated[UserProjectService, Depends(UserProjectService.new_instance)],
        auth_log_service:  Annotated[Auth_Log_Service, Depends(Auth_Log_Service.new_instance)],
        project_service:  Annotated[ProjectService, Depends(ProjectService.new_instance)],
    ):
        return cls(
            invite_link_service=invite_link_service,
            users_service=users_service,
            user_project_service=user_project_service,
            auth_log_service=auth_log_service,
            project_service=project_service,
        )
