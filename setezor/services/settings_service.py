from fastapi import HTTPException
from setezor.schemas.settings import ValueChangeForm
from setezor.unit_of_work.unit_of_work import UnitOfWork


class SettingsService():
    @classmethod
    async def list_admin_settings(cls, uow: UnitOfWork, user_id: str):
        async with uow:
            user = await uow.user.find_one(id=user_id)

        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="Нет доступа")
        async with uow:
            return await uow.setting.list()

    @classmethod
    async def change_setting(cls, uow: UnitOfWork,
                             user_id: str,
                             setting_id: str,
                             change_setting_value_form: ValueChangeForm):
        async with uow:
            user = await uow.user.find_one(id=user_id)

        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="Нет доступа")
        async with uow:
            await uow.setting.edit_one(id=setting_id, data={"field": {"value": change_setting_value_form.value}})
            await uow.commit()
            return await uow.setting.find_one(id=setting_id)
