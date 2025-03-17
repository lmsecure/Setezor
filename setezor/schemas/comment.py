from typing import Optional
from pydantic import BaseModel



class NodeCommentForm(BaseModel):
    ip_id: str
    text: str
    parent_comment_id: Optional[str] = None