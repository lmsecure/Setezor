import json
from Crypto.Random import get_random_bytes
from setezor.tools.password import PasswordTool
from setezor.services.user_service import UsersService
from setezor.unit_of_work import UnitOfWork

class UserManager:
    async def list_users() -> str:
        users = await UsersService.list(uow=UnitOfWork())
        result = {"login": user.login for user in users}
        return json.dumps(result, indent=2)
    
    async def reset_user_password(login: str) -> str:
        uow = UnitOfWork()
        user = await UsersService.get_by_login(uow=uow, login=login)
        if not user:
            return "User does not exist"
        plain_password = get_random_bytes(32).hex()
        hashed_password = PasswordTool.hash(plain_password)
        user = await UsersService.update_user_password(uow=uow, 
                                                       id=user.id, 
                                                       hashed_password=hashed_password)
        return f"New <{login}> password = {plain_password}"