from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from setezor.dependencies.application import is_register_open
from setezor.dependencies.project import access_token_getter, get_user_id
from setezor.managers.auth_manager import AuthManager
from setezor.schemas.auth import RegisterForm
from setezor.schemas.invite_link import InviteLinkCounter

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/login", status_code=200)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_manager: Annotated[AuthManager, Depends(AuthManager.new_instance)],
    response: Response
) -> bool:
    token_pairs = await auth_manager.login(username=form_data.username, password=form_data.password)
    if not token_pairs:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    response.set_cookie(key="access_token", value=token_pairs.get(
        "access_token"), secure=True, httponly=True)
    response.set_cookie(key="refresh_token", value=token_pairs.get(
        "refresh_token"), secure=True, httponly=True)
    return True


@router.post("/logout_from_project", status_code=200)
async def logout_from_project(
    response: Response,
    auth_manager: Annotated[AuthManager, Depends(AuthManager.new_instance)],
    access_token: str = Depends(access_token_getter),
) -> bool:
    token_pairs = await auth_manager.logout_from_project(access_token=access_token)
    response.set_cookie(key="access_token", value=token_pairs.get(
        "access_token"), secure=True, httponly=True)
    response.set_cookie(key="refresh_token", value=token_pairs.get(
        "refresh_token"), secure=True, httponly=True)
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
    auth_manager: Annotated[AuthManager, Depends(AuthManager.new_instance)],
    generate_link_form: InviteLinkCounter,
    user_id: str = Depends(get_user_id)
) -> dict:
    return await auth_manager.generate_register_token(count_of_entries=generate_link_form.count,
                                                      user_id=user_id)


@router.post("/register")
async def register(
    register_form: RegisterForm,
    auth_manager: Annotated[AuthManager, Depends(AuthManager.new_instance)],
    open_reg: bool = Depends(is_register_open)
) -> bool:
    return await auth_manager.register_by_invite_token(open_reg=open_reg,
                                                       register_form=register_form)
