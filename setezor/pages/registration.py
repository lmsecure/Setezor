from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse

from setezor.dependencies.application import is_register_open
from .import TEMPLATES_DIR

router = APIRouter(tags=["Pages"])


@router.get("/registration", response_class=HTMLResponse)
async def registration_page(
    request: Request,
    open_reg: bool = Depends(is_register_open)
):
    if request.cookies.get('access_token'):
        return RedirectResponse('/projects')
    return TEMPLATES_DIR.TemplateResponse(name="registration.html", context={"request": request, "open_reg": open_reg})
