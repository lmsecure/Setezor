from datetime import datetime
from dataclasses import dataclass
from io import BytesIO

from pydantic import BaseModel
from sqlmodel import SQLModel


class ProjectPickForm(BaseModel):
    project_id: str


class ProjectCreateForm(BaseModel):
    name: str


class SearchVulnsSetTokenForm(BaseModel):
    token: str


class EnterTokenForm(BaseModel):
    token: str


@dataclass
class ProjectDTO:
    name: str
    data: dict[str, SQLModel] | BytesIO

    def __post_init__(self):
        mapping = {
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
            'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z', 'И': 'I',
            'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
            'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
            'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch',
            'Ш': 'Sh', 'Щ': 'Shch', 'Ы': 'Y', 'Э': 'E', 'Ю': 'Yu',
            'Я': 'Ya',
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
            'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
            'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
            'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
            'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
            'ш': 'sh', 'щ': 'shch', 'ы': 'y', 'э': 'e', 'ю': 'yu',
            'я': 'ya'
        }
        result_name = ''
        for char in self.name:
            if char in mapping:
                result_name += mapping[char]
            else:
                result_name += char

        self.name = f'project_{result_name}_' + datetime.now().strftime('%d-%m-%Y_%H-%M')
