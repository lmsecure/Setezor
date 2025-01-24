
from fastapi import HTTPException, status
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.tools import JWTManager, PasswordManager
from setezor.services import UsersService, UserProjectService
from setezor.managers import ProjectManager

class AuthService(IService):
    @classmethod
    async def login(cls, uow: UnitOfWork, username: str, password: str):
        if not (user_in_db := await UsersService.get_by_login(uow=uow, login=username)):
            return None
        if not PasswordManager.verify_password(password, user_in_db.hashed_password):
            return None
        access_token = JWTManager.create_access_token(data={"user_id": user_in_db.id})
        refresh_token = JWTManager.create_refresh_token(data={"user_id": user_in_db.id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }
  

    @classmethod
    async def set_current_project(cls, uow: UnitOfWork, project_id: str, user_id: str):
        if not (await ProjectManager.get_by_id(uow=uow, project_id=project_id)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Проект с ID={project_id} не существует")
        if not (await UserProjectService.is_project_available_for_user(uow=uow, project_id=project_id, user_id=user_id)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Тебе сюда нельзя")
        access_token = JWTManager.create_access_token(data={"user_id": user_id, "project_id": project_id})
        refresh_token = JWTManager.create_refresh_token(data={"user_id": user_id, "project_id": project_id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }
    
    @classmethod
    async def set_current_scan(cls, uow: UnitOfWork, project_id: str, user_id: str, scan_id: str):
        if not (await ProjectManager.get_by_id(uow=uow, project_id=project_id)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Проект с ID={project_id} не существует")
        if not (await UserProjectService.is_project_available_for_user(uow=uow, project_id=project_id, user_id=user_id)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Тебе сюда нельзя")
        access_token = JWTManager.create_access_token(data={"user_id": user_id, "project_id": project_id, "scan_id": scan_id})
        refresh_token = JWTManager.create_refresh_token(data={"user_id": user_id, "project_id": project_id, "scan_id": scan_id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }
    
    @classmethod
    async def logout(cls, access_token: str):
        access_token_payload = JWTManager.get_payload(access_token)
        user_id = access_token_payload.get("user_id")
        access_token = JWTManager.create_access_token(data={"user_id": user_id})
        refresh_token = JWTManager.create_refresh_token(data={"user_id": user_id})
        return {
            "refresh_token": refresh_token,
            "access_token": access_token
        }