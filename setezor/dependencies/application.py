from fastapi import HTTPException
from setezor.db.uow_dependency import get_uow
from setezor.schemas.settings import Setting
from setezor.unit_of_work.unit_of_work import UnitOfWork


async def is_register_open() -> bool:
    uow = get_uow()
    open_reg_setting = None
    async with uow:
        open_reg_setting = await uow.setting.find_one(name="open_reg")
    if not open_reg_setting:
        raise HTTPException(status_code=500, detail="Параметр не найден")
    loaded_setting = Setting(**open_reg_setting.model_dump())
    if not isinstance(loaded_setting.field.value, bool):
        raise HTTPException(status_code=500, detail="Некорректный тип параметра")
    return loaded_setting.field.value