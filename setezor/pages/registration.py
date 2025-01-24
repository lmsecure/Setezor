from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from .import TEMPLATES_DIR

router = APIRouter(tags=["Pages"])

@router.get("/registration", response_class=HTMLResponse)
async def registration_page(request: Request):
    return TEMPLATES_DIR.TemplateResponse(name="registration.html", context={"request": request})
