import json
from typing import Annotated
from Crypto.Random import get_random_bytes
from fastapi import Depends
from setezor.services.role_service import RoleService
from setezor.services.user_project_service import UserProjectService
from setezor.tools.password import PasswordTool
from setezor.services.user_service import UsersService

class UserManager:
    def __init__(self,
                 users_service: UsersService,
                 role_service: RoleService,
                 user_project_service: UserProjectService,
                 ):
        self.__users_service = users_service
        self.__role_service = role_service
        self.__user_project_service = user_project_service
        
    async def list_users(self) -> str:
        users = await self.__users_service.list()
        result = [{"login": user.login} for user in users]
        return json.dumps(result, indent=2)
    
    async def reset_user_password(self, login: str) -> str:
        user = await self.__users_service.get_by_login(login=login)
        if not user:
            return "User does not exist"
        plain_password = get_random_bytes(32).hex()
        hashed_password = PasswordTool.hash(plain_password)
        user = await self.__users_service.update_user_password(id=user.id, 
                                             hashed_password=hashed_password)
        return f"New <{login}> password = {plain_password}"
    
    async def get_user_role(self, user_id: str, project_id: str):
        user_in_project = await self.__user_project_service.get_user_project(user_id=user_id, project_id=project_id)
        return await self.__role_service.get(role_id=user_in_project.role_id)

    @classmethod
    def new_instance(
        cls,
        users_service:  Annotated[UsersService, Depends(UsersService.new_instance)],
        user_project_service:  Annotated[UserProjectService, Depends(UserProjectService.new_instance)],
        role_service:  Annotated[RoleService, Depends(RoleService.new_instance)],
    ):
        return cls(
            users_service=users_service,
            role_service=role_service,
            user_project_service=user_project_service,
        )