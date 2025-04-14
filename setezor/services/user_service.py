from setezor.models import User
from setezor.schemas.task import TaskSchema
from fastapi import HTTPException
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List


class UsersService(IService):
    @classmethod
    async def create(cls, uow: UnitOfWork, user: User) -> User:
        users_dict = user.model_dump()
        async with uow:
            user = uow.user.add(users_dict)
            await uow.commit()
            return user

    @classmethod
    async def list(cls, uow: UnitOfWork) -> List[User]:
        async with uow:
            users = await uow.user.list()
            return users


    @classmethod
    async def list_users_in_application(cls, uow: UnitOfWork, user_id: str):
        async with uow:
            user = await uow.user.find_one(id=user_id)
        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        async with uow:
            users = await uow.user.list()
        result = []
        for user in users:
            if user.id != user_id:
                result.append({
                    "id": user.id,
                    "login": user.login
                })
        return result

    @classmethod
    async def get(cls, uow: UnitOfWork, id: int) -> User:
        async with uow:
            user = await uow.user.find_one(id=id)
            return user

    @classmethod
    async def get_by_login(cls, uow: UnitOfWork, login: str) -> User:
        async with uow:
            user = await uow.user.find_one(login=login)
            return user

    @classmethod
    async def get_user_tasks(cls, uow: UnitOfWork, id: int) -> List[TaskSchema]:
        async with uow:
            tasks = await uow.task.filter(user_id=id)
            return tasks

    @classmethod
    async def update_user_password(cls, uow: UnitOfWork, id: str, hashed_password: str):
        async with uow:
            await uow.user.edit_one(id=id, data={"hashed_password": hashed_password})
            await uow.commit()
