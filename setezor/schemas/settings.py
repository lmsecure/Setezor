import enum
from typing import Union
from pydantic import BaseModel


class SettingType(enum.StrEnum):
    boolean = "boolean"
    string = "string"
    integer = "integer"


class ValueField(BaseModel):
    value: Union[int, bool, str]

class Setting(BaseModel):
    name: str
    description: str
    field: ValueField
    value_type: SettingType


class ValueChangeForm(BaseModel):
    value: bool | str | int | float
