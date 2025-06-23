from pydantic import BaseModel
from typing import List

class PaginatedResponse(BaseModel):
    data: List
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool