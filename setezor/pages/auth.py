from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from .import TEMPLATES_DIR

router = APIRouter(tags=["Pages"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return TEMPLATES_DIR.TemplateResponse(name="auth.html", context={"request": request})
