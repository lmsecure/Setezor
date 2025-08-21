from typing import List, Optional

from sqlmodel import desc, func, select

from setezor.models import DNS_A, IP, DNS_A_Screenshot, Domain, Screenshot
from setezor.repositories import SQLAlchemyRepository


class DNS_A_ScreenshotRepository(SQLAlchemyRepository[DNS_A_Screenshot]):
    model = DNS_A_Screenshot

    FIELD_MAPPING = {
        "domain": Domain.domain,
        "ip": IP.ip,
        "screenshot_id": Screenshot.id,
        "screenshot_path": Screenshot.path,
        "created_at": DNS_A_Screenshot.created_at,
    }

    def _build_base_query(self):
        """Создает базовый запрос с выбором только нужных полей для UI"""
        return (
            select(
                DNS_A_Screenshot.id,
                DNS_A_Screenshot.created_at,
                Domain.domain,
                IP.ip,
                Screenshot.id.label("screenshot_id"),
                Screenshot.path.label("screenshot_path"),
            )
            .join(Screenshot, DNS_A_Screenshot.screenshot_id == Screenshot.id)
            .join(DNS_A, DNS_A_Screenshot.dns_a_id == DNS_A.id)
            .join(Domain, DNS_A.target_domain_id == Domain.id)
            .join(IP, DNS_A.target_ip_id == IP.id)
        )

    def _build_count_query(self):
        """Создает упрощенный COUNT запрос"""
        return (
            select(func.count(DNS_A_Screenshot.id))
            .join(DNS_A, DNS_A_Screenshot.dns_a_id == DNS_A.id)
            .join(Domain, DNS_A.target_domain_id == Domain.id)
            .join(IP, DNS_A.target_ip_id == IP.id)
        )

    def _apply_filters(self, stmt, filter_params):
        """Применяет фильтры к запросу"""
        if not filter_params:
            return stmt

        for filter_param in filter_params:
            field = filter_param.get("field")
            type_filter = filter_param.get("type", "=")
            value = filter_param.get("value")

            if field in self.FIELD_MAPPING and value is not None:
                column = self.FIELD_MAPPING[field]
                if type_filter == "=":
                    stmt = stmt.where(column == value)
                elif type_filter == "!=":
                    stmt = stmt.where(column != value)
                elif type_filter == "like":
                    stmt = stmt.where(column.like(f"%{value}%"))
                elif type_filter == ">":
                    stmt = stmt.where(column > value)
                elif type_filter == ">=":
                    stmt = stmt.where(column >= value)
                elif type_filter == "<":
                    stmt = stmt.where(column < value)
                elif type_filter == "<=":
                    stmt = stmt.where(column <= value)
        return stmt

    def _apply_sorting(self, stmt, sort_params):
        """Применяет сортировку к запросу"""
        if not sort_params:
            return stmt.order_by(DNS_A_Screenshot.created_at.desc())

        for sort_param in sort_params:
            field = sort_param.get("field")
            direction = sort_param.get("dir", "asc")

            if field in self.FIELD_MAPPING:
                column = self.FIELD_MAPPING[field]
                if direction == "desc":
                    stmt = stmt.order_by(desc(column))
                else:
                    stmt = stmt.order_by(column)
        return stmt

    async def exists(self, dns_a_screenshot_obj: DNS_A_Screenshot):
        """Проверяет, существует ли уже связь между DNS A записью и скриншотом"""
        if dns_a_screenshot_obj.dns_a_id and dns_a_screenshot_obj.screenshot_id:
            stmt = (
                select(DNS_A_Screenshot.id)
                .where(
                    DNS_A_Screenshot.dns_a_id == dns_a_screenshot_obj.dns_a_id,
                    DNS_A_Screenshot.screenshot_id == dns_a_screenshot_obj.screenshot_id,
                )
                .limit(1)
            )
            result = await self._session.scalar(stmt)
            return result is not None
        return False

    async def get_screenshots_with_info(self, project_id: str):
        """Получить все скриншоты с информацией о доменах и IP для проекта"""
        stmt = (
            self._build_base_query()
            .where(DNS_A_Screenshot.project_id == project_id)
            .order_by(DNS_A_Screenshot.created_at.desc())
        )
        result = await self._session.exec(stmt)
        return result.all()

    async def get_screenshots_by_domain(self, domain: str, project_id: str):
        """Получить скриншоты для конкретного домена"""
        stmt = (
            self._build_base_query()
            .where(DNS_A_Screenshot.project_id == project_id, Domain.domain == domain)
            .order_by(DNS_A_Screenshot.created_at.desc())
        )
        result = await self._session.exec(stmt)
        return result.all()

    async def get_screenshots_by_ip(self, ip: str, project_id: str):
        """Получить скриншоты для конкретного IP"""
        stmt = (
            self._build_base_query()
            .where(DNS_A_Screenshot.project_id == project_id, IP.ip == ip)
            .order_by(DNS_A_Screenshot.created_at.desc())
        )
        result = await self._session.exec(stmt)
        return result.all()

    async def get_screenshots_with_info_paginated(
        self,
        project_id: str,
        scans: List[str],
        page: int,
        size: int,
        sort_params: Optional[List[dict]] = None,
        filter_params: Optional[List[dict]] = None,
    ):
        """Получить скриншоты с пагинацией, фильтрацией и сортировкой"""
        stmt = self._build_base_query().filter(DNS_A_Screenshot.project_id == project_id, DNS_A_Screenshot.scan_id.in_(scans))
        stmt = self._apply_filters(stmt, filter_params)
        stmt = self._apply_sorting(stmt, sort_params)
        stmt = stmt.offset((page - 1) * size).limit(size)

        count_stmt = self._build_count_query().where(DNS_A_Screenshot.project_id == project_id, DNS_A_Screenshot.scan_id.in_(scans))
        count_stmt = self._apply_filters(count_stmt, filter_params)

        total = await self._session.scalar(count_stmt)
        result = await self._session.exec(stmt)

        return total, result.all()
