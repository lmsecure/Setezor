
import string
from fastapi import HTTPException, status
from setezor.interfaces.service import IService
from setezor.schemas.auth import RegisterForm
from setezor.services.invite_link_service import InviteLinkService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.tools import JWT_Tool, PasswordTool
from setezor.services import UsersService, UserProjectService, Auth_Log_Service
from setezor.managers import ProjectManager
from setezor.models import User

class AuthService(IService):
    @classmethod
    async def login(cls, uow: UnitOfWork, username: str, password: str):
        await Auth_Log_Service.log_event(uow=uow, login=username, event="LOGIN ATTEMPT")
        if not (user_in_db := await UsersService.get_by_login(uow=uow, login=username)):
            await Auth_Log_Service.log_event(uow=uow, login=username, event="LOGIN DOES NOT EXIST")
            return None
        if not PasswordTool.verify_password(password, user_in_db.hashed_password):
            await Auth_Log_Service.log_event(uow=uow, login=username, event="INVALID PASSWORD")
            return None
        await Auth_Log_Service.log_event(uow=uow, login=username, event="SUCCESSFUL LOGIN")
        access_token = JWT_Tool.create_access_token(data={"user_id": user_in_db.id})
        refresh_token = JWT_Tool.create_refresh_token(data={"user_id": user_in_db.id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }
  

    @classmethod
    async def set_current_project(cls, uow: UnitOfWork, project_id: str, user_id: str):
        user = await UsersService.get(uow=uow, id=user_id)
        await Auth_Log_Service.log_event(uow=uow, login=user.login, event=f"PROJECT PICK ATTEMPT {project_id}")
        if not (await ProjectManager.get_by_id(uow=uow, project_id=project_id)):
            await Auth_Log_Service.log_event(uow=uow, login=user.login, event=f"NONEXISTENT PROJECT {project_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Проект с ID={project_id} не существует")
        if not (await UserProjectService.get_user_project(uow=uow, project_id=project_id, user_id=user_id)):
            await Auth_Log_Service.log_event(uow=uow, login=user.login, event=f"UNAVAILABLE PROJECT {project_id} FOR USER")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Тебе сюда нельзя")
        await Auth_Log_Service.log_event(uow=uow, login=user.login, event=f"SUCCESSFUL PROJECT {project_id} PICK")
        access_token = JWT_Tool.create_access_token(data={"user_id": user_id, "project_id": project_id})
        refresh_token = JWT_Tool.create_refresh_token(data={"user_id": user_id, "project_id": project_id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }
    
    @classmethod
    async def set_current_scan(cls, uow: UnitOfWork, project_id: str, user_id: str, scan_id: str):
        if not (await ProjectManager.get_by_id(uow=uow, project_id=project_id)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Проект с ID={project_id} не существует")
        if not (await UserProjectService.get_user_project(uow=uow, project_id=project_id, user_id=user_id)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Тебе сюда нельзя")
        access_token = JWT_Tool.create_access_token(data={"user_id": user_id, "project_id": project_id, "scan_id": scan_id})
        refresh_token = JWT_Tool.create_refresh_token(data={"user_id": user_id, "project_id": project_id, "scan_id": scan_id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }
    
    @classmethod
    async def logout_from_project(cls, access_token: str):
        access_token_payload = JWT_Tool.get_payload(access_token)
        user_id = access_token_payload.get("user_id")
        access_token = JWT_Tool.create_access_token(data={"user_id": user_id})
        refresh_token = JWT_Tool.create_refresh_token(data={"user_id": user_id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }
    

    @classmethod
    async def generate_register_token(cls, uow: UnitOfWork, 
                                      count_of_entries: int,
                                      user_id: str) -> dict:
        user = await UsersService.get(uow=uow, id=user_id)
        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="You are not superuser")
        payload = {"event": "register"}
        return await InviteLinkService.create_token(uow=uow, count_of_entries=count_of_entries, payload=payload)

    @classmethod
    async def register_by_invite_token(cls, uow: UnitOfWork, open_reg: bool, register_form: RegisterForm):
        if register_form.password != register_form.password_confirmation:
            raise HTTPException(status_code=400, detail="Password and password confirmation mismatch")
        if not open_reg:
            async with uow:
                invite_link = await uow.invite_link.find_one(token_hash=register_form.invite_token)
            if not invite_link:
                raise HTTPException(status_code=400, detail="Token not found")
            token_payload = JWT_Tool.get_payload(invite_link.token)
            if not token_payload:
                raise HTTPException(status_code=403, detail="Token is expired")
            if not invite_link.count_of_entries:
                raise HTTPException(status_code=403, detail="Invalid token")
        if not all([c in string.ascii_letters + string.digits for c in register_form.login]):
            raise HTTPException(status_code=400, detail="Username can only contain letters and digits")        
        if await UsersService.get_by_login(uow=uow, login=register_form.login):
            raise HTTPException(status_code=400, detail="Username is already taken")
        
        
        if not open_reg:
            event = token_payload.get("event")
            if event == "register":
                async with uow:
                    await uow.invite_link.edit_one(id=invite_link.id, data={"count_of_entries": invite_link.count_of_entries-1})
                    await uow.commit()
        hashed_password = PasswordTool.hash(register_form.password)
        new_user_model = User(
            login=register_form.login,
            hashed_password=hashed_password
        )
        await UsersService.create(uow=uow, user=new_user_model)
        return True