from sqlmodel import select, func, or_, and_
from sqlalchemy.orm import aliased

from setezor.models import Project, UserProject, IP, Port, NodeComment, L4SoftwareVulnerability, Scan
from setezor.repositories import SQLAlchemyRepository


class ProjectRepository(SQLAlchemyRepository[Project]):
    model = Project

    async def get_statistic(self, user_id: str, project_ids: list[str]) -> list:
        result_objs: list = list()
        if not project_ids:
            return result_objs
        addition = [UserProject.project_id == project_id for project_id in project_ids]
        count_ip = (
            select(
                IP.scan_id,
                func.count().label("cnt")
            )
            .group_by(IP.scan_id)
            .subquery()
        )
        count_port = (
            select(
                Port.scan_id,
                func.count().label("cnt")
            )
            .group_by(Port.scan_id)
            .subquery()
        )
        count_comment = (
            select(
                IP.scan_id,
                func.count().label("cnt")
            )
            .join(NodeComment, IP.id == NodeComment.ip_id)
            .group_by(IP.scan_id)
            .subquery()
        )
        count_vuln = (
            select(
                L4SoftwareVulnerability.scan_id,
                func.count().label("cnt")
            )
            .group_by(L4SoftwareVulnerability.scan_id)
            .subquery()
        )
        stmt = (
            select(
                UserProject.project_id.label("project_id"),
                Scan.name.label("scan_name"),
                func.coalesce(count_ip.c.cnt, 0).label("count_ip"),
                func.coalesce(count_port.c.cnt, 0).label("count_port"),
                func.coalesce(count_comment.c.cnt, 0).label("count_comment"),
                func.coalesce(count_vuln.c.cnt, 0).label("count_vuln"),
            ).join(Scan, Scan.project_id == UserProject.project_id)
                .join(count_ip, count_ip.c.scan_id == Scan.id, isouter=True)
                .join(count_port, count_port.c.scan_id == Scan.id, isouter=True)
                .join(count_comment, count_comment.c.scan_id == Scan.id, isouter=True)
                .join(count_vuln, count_vuln.c.scan_id == Scan.id, isouter=True)
            .filter(UserProject.user_id == user_id, or_(*addition))
        )
        result = await self._session.exec(stmt)
        result_objs = result.all() or list()
        return result_objs
