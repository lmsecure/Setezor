from typing import List
from datetime import datetime

from sqlalchemy.sql.functions import func
from sqlmodel import select, or_

from setezor.models import DNS, Domain
from setezor.models.web_archive import WebArchive
from setezor.repositories import SQLAlchemyRepository


class WebArchiveRepository(SQLAlchemyRepository[WebArchive]):
    model = WebArchive

    async def exists(self, web_archive_obj: WebArchive):
        stmt = select(WebArchive).filter(WebArchive.name == web_archive_obj.name)
        result = await self._session.exec(stmt)
        result_obj: WebArchive = result.first()
        if result_obj:
            result_obj.created_at = datetime.now()
            return result_obj

    async def get_web_archive_data(
        self,
        project_id: str,
        scans: List[str],
        page: int,
        size: int,
        sort_params: list = None,
        filter_params: list = None
    ):
        field_mapping = {
            "archive_id": WebArchive.id,
            "domain": Domain.domain,
            "url": WebArchive.url,
        }

        stmt = (select(WebArchive.id, Domain.domain, WebArchive.url)
                .join(DNS, DNS.target_domain_id == Domain.id)
                .join(WebArchive, WebArchive.dns_id == DNS.id)
                .where(WebArchive.project_id == project_id, WebArchive.scan_id.in_(scans))
            )
        if filter_params:
            for filter_item in filter_params:
                field = filter_item.get("field")
                type_op = filter_item.get("type", "=")
                value = filter_item.get("value")

                if field in field_mapping and value is not None:
                    column = field_mapping[field]

                    if isinstance(value, list):
                        if not value:
                            continue

                        if type_op == "=":
                            stmt = stmt.filter(column.in_(value))
                        elif type_op == "!=":
                            stmt = stmt.filter(~column.in_(value))
                        elif type_op == "like":
                            conditions = [
                                column.ilike(f"%{v}%")
                                for v in value
                                if v is not None and v != ""
                            ]
                            if conditions:
                                stmt = stmt.filter(or_(*conditions))
                        else:
                            for v in value:
                                if type_op == ">":
                                    stmt = stmt.filter(column > v)
                                elif type_op == ">=":
                                    stmt = stmt.filter(column >= v)
                                elif type_op == "<":
                                    stmt = stmt.filter(column < v)
                                elif type_op == "<=":
                                    stmt = stmt.filter(column <= v)
                    else:
                        if type_op == "like":
                            if value != "":
                                stmt = stmt.filter(column.ilike(f"%{value}%"))
                        elif type_op == "=":
                            stmt = stmt.filter(column == value)
                        elif type_op == "!=":
                            stmt = stmt.filter(column != value)
                        elif type_op == ">":
                            stmt = stmt.filter(column > value)
                        elif type_op == ">=":
                            stmt = stmt.filter(column >= value)
                        elif type_op == "<":
                            stmt = stmt.filter(column < value)
                        elif type_op == "<=":
                            stmt = stmt.filter(column <= value)

        if sort_params:
            order_clauses = []
            for sort_item in sort_params:
                field = sort_item.get("field")
                direction = sort_item.get("dir", "asc")

                if field in field_mapping:
                    column = field_mapping[field]
                    sorted_column = func.coalesce(column, "")
                    if direction == "desc":
                        order_clauses.append(sorted_column.desc())
                    else:
                        order_clauses.append(sorted_column.asc())

            if order_clauses:
                stmt = stmt.order_by(*order_clauses)

        count_query = select(func.count()).select_from(stmt.alias())
        total = await self._session.scalar(count_query)
        offset = (page - 1) * size
        paginated_query = stmt.offset(offset).limit(size)
        result = await self._session.exec(paginated_query)
        return total, result.all()