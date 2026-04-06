from typing import List

from setezor.models import Task
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import or_, select, desc, func
from sqlalchemy.engine.result import ScalarResult

from setezor.schemas.roles import Roles
from setezor.schemas.task import TaskStatus

class TasksRepository(SQLAlchemyRepository[Task]):
    model = Task


    async def filter(self, *, status, **filter_by):
        stmt = select(self.model).filter(Task.status.in_(status)).filter_by(**filter_by)
        stmt = stmt.order_by(desc(Task.created_at))
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()


    async def count_of_running_tasks_on_agent(self, agent_id: str):
        stmt = select(func.count(Task.id)).where((Task.agent_id == agent_id) & ((Task.status == TaskStatus.processing_on_agent) | (Task.status == TaskStatus.created)))
        res = await self._session.exec(stmt)
        return res.first()

    async def get_tasks_data(
        self,
        project_id: str,
        user_role: Roles,
        statuses: List[str],
        page: int,
        size: int,
        sort_params: list = None,
        filter_params: list = None
    ):
        field_mapping = {
            "task_id": Task.id,
            "created_by": Task.created_by,
            "created_at": Task.created_at,
            "updated_at": Task.updated_at,
            "params": Task.params,
            "error": Task.traceback,
            "scan_id": Task.scan_id
        }
        selected_fields = [Task.id, Task.created_by, Task.created_at,
                           Task.updated_at, Task.params, Task.traceback, Task.scan_id]
        if user_role == Roles.owner:
            field_mapping["user_id"] = Task.user_id
            selected_fields.append(Task.user_id)

        stmt = (select(*selected_fields)
                .where(Task.project_id == project_id, Task.status.in_(statuses))
                .order_by(desc(Task.created_at)))

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