from fastapi import APIRouter, Depends

from setezor.dependencies.project import get_user_id
from setezor.dependencies.uow_dependency import UOWDep
from setezor.services.user_service import UsersService


router = APIRouter(prefix="/user", tags=["User"])


@router.get("")
async def list_user_in_application(
    uow: UOWDep,
    user_id: str = Depends(get_user_id),
) -> list:
    return await UsersService.list_users_in_application(uow=uow, user_id=user_id)