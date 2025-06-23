from typing import Annotated
from fastapi import APIRouter, Depends

from setezor.dependencies.project import get_user_id
from setezor.models.settings import Settings
from setezor.schemas.settings import ValueChangeForm
from setezor.services import SettingsService


router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/admin")
async def list_admin_settings(
    settings_service: Annotated[SettingsService, Depends(SettingsService.new_instance)],
    user_id: str = Depends(get_user_id)
) -> list[Settings]:
    return await settings_service.list_admin_settings(user_id=user_id)

@router.patch("/admin/{setting_id}")
async def update_setting(
    settings_service: Annotated[SettingsService, Depends(SettingsService.new_instance)],
    setting_id: str,
    change_setting_value_form: ValueChangeForm,
    user_id: str = Depends(get_user_id)
) -> Settings:
    return await settings_service.change_setting(user_id=user_id,
                                                setting_id=setting_id,
                                                change_setting_value_form=change_setting_value_form)