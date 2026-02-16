from typing import Annotated
from fastapi import APIRouter, Depends

from setezor.dependencies.project import get_user_id
from setezor.services.user_service import UsersService


router = APIRouter(prefix="/user", tags=["User"])


@router.get("")
async def list_user_in_application(
    users_service: Annotated[UsersService, Depends(UsersService.new_instance)],
    user_id: str = Depends(get_user_id),
) -> list:
    return await users_service.list_users_in_application(user_id=user_id)

@router.get("/me")
async def my_user(
    user_id: str = Depends(get_user_id),
) -> str:
    return user_id