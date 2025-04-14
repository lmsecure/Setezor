from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from setezor.dependencies.application import is_register_open
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import access_token_getter, get_user_id
from setezor.schemas.auth import RegisterForm
from setezor.schemas.invite_link import InviteLinkCounter
from setezor.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/login", status_code=200)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    uow: UOWDep,
    response: Response
) -> bool:
    token_pairs = await AuthService.login(uow=uow, username=form_data.username, password=form_data.password)
    if not token_pairs:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    response.set_cookie(key="access_token", value=token_pairs.get("access_token"), secure=True, httponly=True)
    response.set_cookie(key="refresh_token", value=token_pairs.get("refresh_token"), secure=True, httponly=True)
    return True


@router.post("/logout_from_project", status_code=200)
async def logout_from_project(
    response: Response,
    access_token: str = Depends(access_token_getter),
) -> bool:
    token_pairs = await AuthService.logout_from_project(access_token=access_token)
    response.set_cookie(key="access_token", value=token_pairs.get("access_token"), secure=True, httponly=True)
    response.set_cookie(key="refresh_token", value=token_pairs.get("refresh_token"), secure=True, httponly=True)
    return True

@router.post("/logout_from_profile", status_code=200)
async def logout_from_profile(
    response: Response,
    access_token: str = Depends(access_token_getter),
) -> bool:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return True

@router.post("/generate_register_token", status_code=200)
async def generate_register_token(
    uow: UOWDep, 
    generate_link_form: InviteLinkCounter,
    user_id: str = Depends(get_user_id)
) -> dict:
    return await AuthService.generate_register_token(uow=uow, 
                                                     count_of_entries=generate_link_form.count,
                                                     user_id=user_id)


@router.post("/register")
async def register(
    register_form: RegisterForm,
    uow: UOWDep,
    open_reg: bool = Depends(is_register_open)
) -> bool:
    return await AuthService.register_by_invite_token(uow=uow, 
                                                      open_reg=open_reg,
                                                      register_form=register_form)