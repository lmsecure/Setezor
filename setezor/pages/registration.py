from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from setezor.dependencies.application import is_register_open
from .import TEMPLATES_DIR

router = APIRouter(tags=["Pages"])


@router.get("/registration", response_class=HTMLResponse)
async def registration_page(
    request: Request,
    open_reg: bool = Depends(is_register_open)
):
    return TEMPLATES_DIR.TemplateResponse(name="registration.html", context={"request": request, "open_reg": open_reg})
