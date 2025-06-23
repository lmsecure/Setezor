from typing import List, Optional
from sqlmodel import Field, Relationship
from setezor.models.ip import IP
from .import IDDependent, TimeDependent, ProjectDependent

class NodeComment(IDDependent, TimeDependent, ProjectDependent, table=True):
    __tablename__ = "network_ip_node_comment"
    __table_args__ = {
        "comment": "Таблица предназначена для комментариев на узле на карте сети"
    }
    
    ip_id: str = Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор ip адреса"})
    parent_comment_id: Optional[str] = Field(foreign_key="network_ip_node_comment.id", sa_column_kwargs={"comment":"Идентификатор родительского коммента"})
    user_id: str = Field(foreign_key="user.id", sa_column_kwargs={"comment":"Идентификатор пользователя, оставившего коммент"})

    text: str = Field(sa_column_kwargs={"comment":"Комментарий"})
