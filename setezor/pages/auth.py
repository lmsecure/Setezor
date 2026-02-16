from fastapi import APIRouter, Request, Depends, Response
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse

from .import TEMPLATES_DIR
from ..services import UsersService
from ..tools import JWT_Tool

router = APIRouter(tags=["Pages"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    response: Response,
    user_service: UsersService = Depends(UsersService.new_instance),
):
    auth_page = TEMPLATES_DIR.TemplateResponse(name="auth.html", context={"request": request})
    access_token = request.cookies.get('access_token')
    if access_token:
        if not JWT_Tool.is_expired(access_token):
            user_id = JWT_Tool.get_payload(access_token).get('user_id')
            if user_id:
                user = await user_service.get(user_id)
                if user:
                    return RedirectResponse('/projects')

    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return auth_page
