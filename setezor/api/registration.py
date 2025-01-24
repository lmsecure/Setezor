from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from setezor.api.dependencies import UOWDep
from setezor.schemas.user import UserAuth
from setezor.dependencies.project import access_token_getter
from setezor.services.auth_service import AuthService
from fastapi.responses import RedirectResponse

router = APIRouter(
    prefix="/registration",
    tags=["Registration"],
)


@router.post("/registration", status_code=200)
async def registration(
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


@router.post("/logout", status_code=200)
async def logout(
    response: Response,
    access_token: str = Depends(access_token_getter),
) -> bool:
    token_pairs = await AuthService.logout(access_token=access_token)
    response.set_cookie(key="access_token", value=token_pairs.get("access_token"), secure=True, httponly=True)
    response.set_cookie(key="refresh_token", value=token_pairs.get("refresh_token"), secure=True, httponly=True)
    return True