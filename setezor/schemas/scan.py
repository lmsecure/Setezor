from typing import Optional
from pydantic import BaseModel


class ScanPickForm(BaseModel):
    scan_id: str


class ScanCreateForm(BaseModel):
    name: str
    description: Optional[str] = ""