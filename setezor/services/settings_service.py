from fastapi import HTTPException
from setezor.services.base_service import BaseService
from setezor.schemas.settings import ValueChangeForm
from setezor.unit_of_work.unit_of_work import UnitOfWork


class SettingsService(BaseService):
    async def list_admin_settings(self, user_id: str):
        async with self._uow:
            user = await self._uow.user.find_one(id=user_id)

        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="Нет доступа")
        async with self._uow:
            return await self._uow.setting.list()

    async def change_setting(self,
                             user_id: str,
                             setting_id: str,
                             change_setting_value_form: ValueChangeForm):
        async with self._uow:
            user = await self._uow.user.find_one(id=user_id)

        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="Нет доступа")
        async with self._uow:
            await self._uow.setting.edit_one(id=setting_id, data={"field": {"value": change_setting_value_form.value}})
            await self._uow.commit()
            return await self._uow.setting.find_one(id=setting_id)
