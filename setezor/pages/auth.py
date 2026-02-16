from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse

from .import TEMPLATES_DIR

router = APIRouter(tags=["Pages"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.cookies.get('access_token'):
        return RedirectResponse('/projects')
    return TEMPLATES_DIR.TemplateResponse(name="auth.html", context={"request": request})
