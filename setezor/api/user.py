from typing import Annotated
from fastapi import APIRouter, Depends

from setezor.dependencies.project import get_user_id
from setezor.services.user_service import UsersService
from setezor.services.user_project_service import UserProjectService


router = APIRouter(prefix="/user", tags=["User"])



@router.get("/projects")
async def list_user_projects(
    user_project_service: Annotated[UserProjectService, Depends(UserProjectService.new_instance)],
    user_id: str = Depends(get_user_id),
) -> list[dict]:
    list_projects: list = await user_project_service.get_user_projects(user_id=user_id)
    return list_projects



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