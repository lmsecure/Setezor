from fastapi import APIRouter, Depends

from setezor.dependencies.project import get_user_id
from setezor.dependencies.uow_dependency import UOWDep
from setezor.models.settings import Settings
from setezor.schemas.settings import ValueChangeForm
from setezor.services import SettingsService


router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/admin")
async def list_admin_settings(
    uow: UOWDep,
    user_id: str = Depends(get_user_id)
) -> list[Settings]:
    return await SettingsService.list_admin_settings(uow=uow, user_id=user_id)

@router.patch("/admin/{setting_id}")
async def update_setting(
    uow: UOWDep,
    setting_id: str,
    change_setting_value_form: ValueChangeForm,
    user_id: str = Depends(get_user_id)
) -> Settings:
    return await SettingsService.change_setting(uow=uow, 
                                                user_id=user_id,
                                                setting_id=setting_id,
                                                change_setting_value_form=change_setting_value_form)