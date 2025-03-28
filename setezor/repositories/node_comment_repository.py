from sqlmodel import select, distinct

from setezor.models import NodeComment, User
from setezor.repositories import SQLAlchemyRepository

class NodeCommentRepository(SQLAlchemyRepository[NodeComment]):
    model = NodeComment

    async def for_node(self, ip_id: str, project_id: str, hide_deleted: bool):
        stmt = select(NodeComment, User.login).where(NodeComment.ip_id == ip_id,
                                         NodeComment.project_id == project_id).join(User, User.id == NodeComment.user_id).order_by(NodeComment.created_at)
        if hide_deleted:
            stmt = stmt.filter(NodeComment.deleted_at == None)
        result = await self._session.exec(stmt)
        return result
    
    async def list_nodes_with_comment(self, project_id: str):
        stmt = select(distinct(NodeComment.ip_id)).filter(NodeComment.project_id == project_id)
        result = await self._session.exec(stmt)
        return result