from setezor.models import User
from setezor.schemas.task import TaskSchema
from fastapi import HTTPException
from setezor.services.base_service import BaseService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List


class UsersService(BaseService):
    async def create(self, user: User) -> User:
        users_dict = user.model_dump()
        async with self._uow:
            user = self._uow.user.add(users_dict)
            await self._uow.commit()
            return user

    async def list(self) -> List[User]:
        async with self._uow:
            users = await self._uow.user.list()
            return users

    async def list_users_in_application(self, user_id: str):
        async with self._uow:
            user = await self._uow.user.find_one(id=user_id)
        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        async with self._uow:
            users = await self._uow.user.list()
        result = []
        for user in users:
            if user.id != user_id:
                result.append({
                    "id": user.id,
                    "login": user.login
                })
        return result


    async def get(self, user_id: int) -> User:
        async with self._uow:
            user = await self._uow.user.find_one(id=user_id)
            return user


    async def get_by_login(self, login: str) -> User:
        async with self._uow:
            user = await self._uow.user.find_one(login=login)
            return user

    async def get_user_tasks(self, id: int) -> List[TaskSchema]:
        async with self._uow:
            tasks = await self._uow.task.filter(user_id=id)
            return tasks

    async def update_user_password(self, id: str, hashed_password: str):
        async with self._uow:
            await self._uow.user.edit_one(id=id, data={"hashed_password": hashed_password})
            await self._uow.commit()
