from typing import Annotated
from fastapi import APIRouter, Depends, Request
from setezor.dependencies.project import get_user_id
from setezor.services.user_service import UsersService
from .import TEMPLATES_DIR

router = APIRouter(tags=["Pages"])

@router.get('/admin_settings')
async def admin_settings_page(
    request: Request,
    users_service: Annotated[UsersService, Depends(UsersService.new_instance)],
    user_id: str = Depends(get_user_id),
):
    """Формирует html страницу отображения топологии сети на основе jinja2 шаблона и возвращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    user = await users_service.get(user_id=user_id)
    context = {
        "request": request,
        'user': user
    }
    return TEMPLATES_DIR.TemplateResponse(name="settings/admin_settings.html", context=context)