import uuid
import json
from typing import Dict, List, Optional
from setezor.services.base_service import BaseService
from setezor.unit_of_work import UnitOfWork
import orjson


class AnalyticsService(BaseService):
    async def get_last_scan_id(self, project_id: str):
        async with self._uow:
            last_scan = await self._uow.scan.last(project_id=project_id)
            return last_scan.id


    async def get_whois_data(self, project_id: uuid.UUID) -> Dict:
        ''' TODO Функция для получения данных из whois сделанный перед нг, потом его нужно будет запихнуть куда нибудь в нормальное место'''
        async with self._uow:
            whois_ip_data = await self._uow.whois_ip.get_whois_ip_data(project_id=project_id)
            whois__transform_ip_data = {
                    'domain_crt': [i[0] for i in whois_ip_data],
                    'netname': [json.loads(i[1]).get('netname') for i in whois_ip_data],
                    'data': [i[1] for i in whois_ip_data],
                    'AS': [i[2] for i in whois_ip_data],
                    'range_ip': [i[3] for i in whois_ip_data],
            }
            whois_domain_data = await self._uow.whois_domain.get_whois_domain_data(project_id=project_id)
            whois_transform_domain_data= {
                'domain_crt': [i[0] for i in whois_domain_data],
                'netname': [json.loads(i[1]).get('netname') for i in whois_domain_data],
                'data': [i[1] for i in whois_domain_data],
            }
            context = {
                'whois_ip_data': whois__transform_ip_data,
                'whois_domain_data': whois_transform_domain_data,
                }
            return context


    async def get_device_types(self, scans: list[str], project_id: str) -> Dict:
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            result = await self._uow.object.get_most_frequent_values_device_type(project_id=project_id, scans=scans)
            device_types = [{"labels": row[0], "data": row[1]} for row in result]
            return {
                "data": [item["data"] for item in device_types],
                "labels": [item["labels"] for item in device_types]
            }


    async def get_object_count(self, scans: list[str], project_id: str) -> int:
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            return await self._uow.object.get_object_count(project_id=project_id, scans=scans)


    async def get_ip_count(self, scans: list[str], project_id: str) -> int:
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            return await self._uow.ip.get_ip_count(project_id=project_id, scans=scans)


    async def get_mac_count(self, scans: list[str], project_id: str) -> int:
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            return await self._uow.mac.get_mac_count(project_id=project_id, scans=scans)


    async def get_port_count(self, scans: list[str], project_id: str) -> int:
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            return await self._uow.port.get_port_count(project_id=project_id, scans=scans)

    async def get_software_version_cpe(self, scans: list[str], project_id: str) -> Dict:
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            result = await self._uow.software.get_software_version_cpe(project_id=project_id, scans=scans)
            return {
                'product': [i[0] for i in result],
                'version': [i[1] for i in result],
                'cpe23': [i[2] for i in result],
                'data': [i[3] for i in result]
            }

    async def get_top_products(self, project_id: str, scans: list[str] | None = None) -> List:
        async with self._uow:
            if not scans:
                scans = [await self.get_last_scan_id(project_id=project_id)]
            return await self._uow.software.get_top_products(project_id=project_id, scans=scans)

    async def get_top_ports(self, project_id: str, scans: list[str] | None = None) -> List:
        async with self._uow:
            if not scans:
                scans = [await self.get_last_scan_id(project_id=project_id)]
            return await self._uow.port.get_top_ports(project_id=project_id, scans=scans)

    async def get_top_protocols(self, project_id: str, scans: list[str] | None = None) -> List:
        async with self._uow:
            if not scans:
                scans = [await self.get_last_scan_id(project_id=project_id)]
            return await self._uow.port.get_top_protocols(project_id=project_id, scans=scans)

    async def get_vulnerabilities(self, scans: list[str], project_id: str) -> Dict:
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            result = await self._uow.vulnerability.get_vulnerabilities(project_id=project_id, scans=scans)
            return {
                'name': [i[0] for i in result],
                'cve': [i[1] for i in result],
                'description': [i[2] for i in result],
                'cvss_score': [i[3] for i in result]
            }

    async def get_ports_and_protocols(self, scans: list[str], project_id: str) -> Dict:
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            result = await self._uow.l4_software.get_ports_and_protocols(project_id=project_id, scans=scans)
            labels = []
            parents = []
            graph_values = []
            for label, parent, value in result:
                labels.append(label)
                parents.append(parent)
                graph_values.append(value)
            return {
                "labels": orjson.dumps(labels).decode(),
                "parents": orjson.dumps(parents).decode(),
                "graph_values": graph_values
            }

    async def get_products_and_service_name(self,  scans: list[str], project_id: str) -> Dict:
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            result = await self._uow.l4_software.get_product_service_name_info_from_sunburts(project_id=project_id, scans=scans)
            labels = []
            parents = []
            graph_values = []
            for label, parent, value in result:
                if parent:
                    labels.append(label)
                else:
                    labels.append(label.capitalize())
                parents.append(parent.capitalize())
                graph_values.append(value)
            return {
                "labels": orjson.dumps(labels).decode(),
                "parents": orjson.dumps(parents).decode(),
                "graph_values": graph_values
            }

    async def get_l4_software_tabulator_data(
        self, 
        project_id: str, 
        scans: list[str],
        page: int,
        size: int, 
        sort: str = "[]", 
        filter: str = "[]"
    ) -> tuple[int, list]:
        try:
            sort_params = json.loads(sort) if sort != "[]" else []
            filter_params = json.loads(filter) if filter != "[]" else []
        except json.JSONDecodeError:
            sort_params = []
            filter_params = []
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            total, rows = await self._uow.l4_software.get_l4_software_tabulator_data(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params or [],
                filter_params=filter_params or []
            )
            
            keys = [
                "id",
                "ipaddr",
                "domain",
                "port",
                "protocol",
                "state",
                "service_name",
                "vendor",
                "product",
                "type",
                "version",
                "build",
                "patch",
                "platform",
                "cpe23"
            ]

            tabulator_transform_dashboard_data = [
                dict(zip(keys, row)) for row in rows
            ]
            return total, tabulator_transform_dashboard_data

    async def get_ip_mac_port_tabulator_data(
        self, 
        project_id: str,
        scans: list[str], 
        page: int, 
        size: int, 
        sort: str = "[]", 
        filter: str = "[]"
    ) -> tuple[int, list]:
        try:
            sort_params = json.loads(sort) if sort != "[]" else []
            filter_params = json.loads(filter) if filter != "[]" else []
        except json.JSONDecodeError:
            sort_params = []
            filter_params = []
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            total, tabulator_dashboard_data = await self._uow.ip.get_ip_mac_port_data(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params or [],
                filter_params=filter_params or [])
        tabulator_transform_dashboard_data = []
        for index, row in enumerate(tabulator_dashboard_data, start=1 + (page - 1) * size):
            tabulator_transform_dashboard_data.append({
                "id": index,
                "ipaddr": row[0],
                "port": row[1],
                "mac" : row[2]
            })
        return total, tabulator_transform_dashboard_data

    async def get_domain_ip_tabulator_data(
        self, 
        project_id: str,
        scans: list[str], 
        page: int, 
        size: int, 
        sort: str = "[]", 
        filter: str = "[]"
    ) -> tuple[int, list]:
        try:
            sort_params = json.loads(sort) if sort != "[]" else []
            filter_params = json.loads(filter) if filter != "[]" else []
        except json.JSONDecodeError:
            sort_params = []
            filter_params = []
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            total, tabulator_dashboard_data = await self._uow.ip.get_domain_ip_data(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params or [],
                filter_params=filter_params or [])
        tabulator_transform_dashboard_data = []
        for index, row in enumerate(tabulator_dashboard_data, start=1 + (page - 1) * size):
            tabulator_transform_dashboard_data.append({
                "id": index,
                "ipaddr": row[0],
                "port": row[1],
                "domain": row[2],
                "DNS": row[3],
                "value": row[4],
                "extra_data": row[5],
                "ip_id": row[6],
                "comments_count": row[7],
            })

        return total, tabulator_transform_dashboard_data

    async def get_l4_soft_vuln_link_tabulator_data(
        self, 
        project_id: str, 
        scans: list[str],
        page: int, 
        size: int, 
        sort: str = "[]", 
        filter: str = "[]"
    ) -> tuple[int, list]:
        try:
            sort_params = json.loads(sort) if sort != "[]" else []
            filter_params = json.loads(filter) if filter != "[]" else []
        except json.JSONDecodeError:
            sort_params = []
            filter_params = []
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            total, rows = await self._uow.l4_software.get_soft_vuln_link_data(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params or [],
                filter_params=filter_params or [])
        keys = [ "vendor", "product", "type", "version", "build", "cpe23", "vulnerability_name", "cve", "cwe", "link", ]
        tabulator_transform_dashboard_data = [
                dict(zip(keys, row)) for row in rows
            ]
        return total, tabulator_transform_dashboard_data
    
    async def get_auth_credentials(
        self, 
        project_id: str, 
        scans: list[str],
        page: int, 
        size: int, 
        sort: str = "[]", 
        filter: str = "[]"
    ) -> tuple[int, list]:
        try:
            sort_params = json.loads(sort) if sort != "[]" else []
            filter_params = json.loads(filter) if filter != "[]" else []
        except json.JSONDecodeError:
            sort_params = []
            filter_params = []
        result = []
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            total, data = await self._uow.authentication_credentials.get_data_for_tabulator(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params or [],
                filter_params=filter_params or []
            )
        for id, item in enumerate(data, start=(page - 1) * size + 1):
            ip, domain, port, auth = item
            result.append({
                    "id" : id,
                    "ipaddr" : ip.ip,
                    "domain" : domain.domain,
                    "port" : port.port,
                    "login" : auth.login,
                    "passwords" : auth.password,
                    "permissions" : ("no permissions", "read", "write", "read/write")[auth.permissions],
                    "parameters" : auth.parameters })
        return total, result

    async def get_dns_a_screenshot_tabulator_data_optimized(
        self, 
        project_id: str,
        scans: list[str], 
        page: int, 
        size: int, 
        sort: str = "[]", 
        filter: str = "[]"
    ) -> tuple[int, list]:
        sort_params = json.loads(sort)
        filter_params = json.loads(filter)
        
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            total, screenshots_data = await self._uow.dns_a_screenshot.get_screenshots_with_info_paginated(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params,
                filter_params=filter_params
            )
        
        tabulator_transform_dashboard_data = []
        for index, row in enumerate(screenshots_data, start=(page - 1) * size + 1):
            dns_a_screenshot_id, created_at, domain, ip, screenshot_path = row
            
            tabulator_transform_dashboard_data.append({
                "id": index,
                "domain": domain,
                "ip": ip,
                "screenshot_path": screenshot_path,
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "",
            })

        return total, tabulator_transform_dashboard_data
    
    async def get_whois_tabulator_data(
        self,
        project_id: str,
        scans: list[str],
        page: int,
        size: int,
        sort: str = "[]",
        filter: str = "[]"
    ) -> tuple[int, list]:
        sort_params = json.loads(sort)
        filter_params = json.loads(filter)
        
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
                
            total, whois_data = await self._uow.dns.get_all_whois_data_independent(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params,
                filter_params=filter_params
            )
            tabulator_transform_whois_data = []
            for index, row_data in enumerate(whois_data, start=(page - 1) * size + 1):
                tabulator_transform_whois_data.append({
                    "id": index,
                    "ipaddr": row_data.get("ipaddr"),
                    "domain": row_data.get("domain"),
                    "AS": row_data.get("AS"),
                    "org-name": row_data.get("org_name"),
                    "data": row_data.get("data"),
                    "range_ip": row_data.get("range_ip"),
                    "source": row_data.get("source"),
                })
            
            return total, tabulator_transform_whois_data
        
    async def get_cve_tabulator_data(
        self, 
        project_id: str, 
        scans: list[str],
        page: int, 
        size: int, 
        sort: str = "[]", 
        filter: str = "[]"
    ) -> tuple[int, list]:
        try:
            sort_params = json.loads(sort) if sort != "[]" else []
            filter_params = json.loads(filter) if filter != "[]" else []
        except json.JSONDecodeError:
            sort_params = []
            filter_params = []
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            total, rows = await self._uow.l4_software.get_cve_data(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params or [],
                filter_params=filter_params or [])
        keys = ["id", "ipaddr", "product", "version", "cve", "cvss3", "cvss3_score", "link"]
        tabulator_transform_cve_data = [
            dict(zip(keys, [i] + list(row))) for i, row in enumerate(rows, 1)
        ]
        return total, tabulator_transform_cve_data
    
    async def get_web_tabulator_data(
        self,
        project_id: str,
        scans: list[str],
        page: int,
        size: int,
        sort: str = "[]",
        filter: str = "[]"
    ) -> tuple[int, list]:
        try:
            sort_params = json.loads(sort) if sort != "[]" else []
            filter_params = json.loads(filter) if filter != "[]" else []
        except json.JSONDecodeError:
            sort_params = []
            filter_params = []
        
        async with self._uow:
            if (not scans) and (last_scan := await self._uow.scan.last(project_id=project_id)):
                scans.append(last_scan.id)
            
            total, rows = await self._uow.l4_software.get_web_data(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params or [],
                filter_params=filter_params or []
            )
            
            port_ids = [row[5] for row in rows]
            all_links = await self._uow.vulnerability_link.get_by_port_ids(
                project_id=project_id,
                scans=scans,
                port_ids=port_ids
            )
            
            tabulator_transform_web_data = []

            for index, row in enumerate(rows, start=(page - 1) * size + 1):
                port_id = row[5]
                port_links = all_links.get(port_id, [])
                links_str = ", ".join(port_links) if port_links else ""

                row_data = {
                    "id": index,
                    "ipaddr": row[0],
                    "domain": row[1],
                    "port": row[2],
                    "product": row[3],
                    "ip_id": row[4],
                    "port_id": row[5],
                    "link": links_str,
                    "comments_count": row[6]
                }

                tabulator_transform_web_data.append(row_data)

            return total, tabulator_transform_web_data

        
    @classmethod
    def get_l4_software_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'port', 'title': 'PORT', "headerFilter": "number", "headerFilterPlaceholder": "Search port...", "headerFilterFunc": "like"},
            {'field': 'state', 'title': 'STATE', "headerFilter": "input", "headerFilterPlaceholder": "Search state..."},
            {'field': 'protocol', 'title': 'PROTOCOL', "headerFilter": "input", "headerFilterPlaceholder": "Search protocol..."},
            {'field': 'service_name', 'title': 'SERVICE_NAME', "headerFilter": "input", "headerFilterPlaceholder": "Search service..."},
            {'field': 'vendor', 'title': 'VENDOR', "headerFilter": "input", "headerFilterPlaceholder": "Search vendor..."},
            {'field': 'product', 'title': 'PRODUCT', "headerFilter": "input", "headerFilterPlaceholder": "Search product..."},
            {'field': 'version', 'title': 'VERSION', "headerFilter": "input", "headerFilterPlaceholder": "Search version..."},
            {'field': 'os', 'title': 'OS', "headerFilter": "input", "headerFilterPlaceholder": "Search OS..."},
            {'field': 'is_secured', 'title': 'is_secured', "headerFilter":"select", "headerFilterPlaceholder": "Select true/false", 'headerFilterParams': {'values': [True, False]}},
        ]

    @classmethod
    def get_ip_mac_port_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'port', 'title': 'PORT', "headerFilter": "number", "headerFilterPlaceholder": "Search port...", "headerFilterFunc": "like"},
            {'field': 'mac', 'title': 'MAC', "headerFilter": "input", "headerFilterPlaceholder": "Search MAC..."},
        ]
    
    @classmethod
    def get_domain_ip_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'port', 'title': 'PORT', "headerFilter": "number", "headerFilterPlaceholder": "Search port...", "headerFilterFunc": "like"},
            {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'DNS', 'title': 'DNS', "headerFilter": "input", "headerFilterPlaceholder": "Search DNS..."},
            {'field': 'value', 'title': 'VALUE', "headerFilter": "input", "headerFilterPlaceholder": "Search value..."},
            {'field': 'extra_data', 'title': 'EXTRA DATA', "headerFilter": "input", "headerFilterPlaceholder": "Search extra data..."},
            {'field': 'comments', 'title': 'Comments'},
        ]


    @classmethod
    def get_soft_vuln_link_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'vendor', 'title': 'VENDOR', "headerFilter": "input", "headerFilterPlaceholder": "Search vendor..."},
            {'field': 'product', 'title': 'PRODUCT', "headerFilter": "input", "headerFilterPlaceholder": "Search product..."},
            {'field': 'type', 'title': 'TYPE', "headerFilter": "input", "headerFilterPlaceholder": "Search type..."},
            {'field': 'version', 'title': 'VERSION', "headerFilter": "input", "headerFilterPlaceholder": "Search version..."},
            {'field': 'build', 'title': 'BUILD', "headerFilter": "input", "headerFilterPlaceholder": "Search build..."},
            {'field': 'cpe23', 'title': 'CPE23', "headerFilter": "input", "headerFilterPlaceholder": "Search CPE..."},
            {'field': 'vulnerability_name', 'title': 'VULN_NAME', "headerFilter": "input", "headerFilterPlaceholder": "Search vuln name..."},
            {'field': 'cve', 'title': 'CVE', "headerFilter": "input", "headerFilterPlaceholder": "Search CVE..."},
            {'field': 'cwe', 'title': 'CWE', "headerFilter": "input", "headerFilterPlaceholder": "Search CWE..."},
            {'field': 'link', 'title': 'LINK', "headerFilter": "input", "headerFilterPlaceholder": "Search link..."},
        ]

    @classmethod
    def get_auth_credentials_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'port', 'title': 'PORT', "headerFilter": "number", "headerFilterPlaceholder": "Search port...", "headerFilterFunc": "like"},
            {'field': 'login', 'title': 'LOGIN', "headerFilter": "input", "headerFilterPlaceholder": "Search login..."},
            {'field': 'password', 'title': 'PASSWORD', "headerFilter": "input", "headerFilterPlaceholder": "Search password..."},
            {'field': 'permissions', 'title': 'PERMISSIONS', "headerFilter": "number", "headerFilterPlaceholder": "Search permissions..."},
            {'field': 'parameters', 'title': 'PARAMETERS', "headerFilter": "input", "headerFilterPlaceholder": "Search parameters..."},
        ]
    
    @classmethod
    def get_dns_a_screenshot_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'ip', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'screenshot_path', 'title': 'SCREENSHOT_PATH'},
            {'field': 'created_at', 'title': 'CREATED_AT', "headerFilter": "input", "headerFilterPlaceholder": "Search date..."},
        ]

    # Пинтестеры

    @classmethod
    def get_whois_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'WHOIS IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'domain', 'title': 'WHOIS Domain', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'range_ip', 'title': 'Range IP', "headerFilter": "input", "headerFilterPlaceholder": "Search range..."},
            {'field': 'AS', 'title': 'AS', "headerFilter": "input", "headerFilterPlaceholder": "Search AS..."},
            {'field': 'org-name', 'title': 'Org-name', "headerFilter": "input", "headerFilterPlaceholder": "Search org..."},
            {'field': 'data', 'title': 'Data', "headerFilter": "input", "headerFilterPlaceholder": "Search data..."},
        ]
    
    @classmethod
    def get_web_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'domain', 'title': 'Domain', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'port', 'title': 'Ports', "headerFilter": "number", "headerFilterPlaceholder": "Search ports...", "headerFilterFunc": "like"},
            {'field': 'code', 'title': 'Code', "headerFilter": "input", "headerFilterPlaceholder": "Search code..."},
            {'field': 'product', 'title': 'Software', "headerFilter": "input", "headerFilterPlaceholder": "Search software..."},
            {'field': 'waf', 'title': 'WAF', "headerFilter": "input", "headerFilterPlaceholder": "Search WAF..."},
            {'field': 'is_vuln_scanned', 'title': 'Is vuln scanned', "headerFilter":"select", "headerFilterPlaceholder": "Select true/false", 'headerFilterParams': {'values': [True, False]}},
            {'field': 'link', 'title': 'Vuln and exploits'},
            {'field': 'comments', 'title': 'Comments'},
        ]
    
    @classmethod
    def get_api_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'domain', 'title': 'Domain', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'api_dir', 'title': 'API Dir', "headerFilter": "input", "headerFilterPlaceholder": "Search dir..."},
            {'field': 'api_endpoint', 'title': 'API Endpoint', "headerFilter": "input", "headerFilterPlaceholder": "Search endpoint..."},
            {'field': 'http_method', 'title': 'HTTP Method', "headerFilter": "input", "headerFilterPlaceholder": "GET/POST..."},
            {'field': 'body', 'title': 'body', "headerFilter": "input", "headerFilterPlaceholder": "Search body..."},
            {'field': 'comments', 'title': 'Comments'},
        ]
    
    @classmethod
    def get_cve_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'product', 'title': 'Software', "headerFilter": "input", "headerFilterPlaceholder": "Search software..."},
            {'field': 'version', 'title': 'Version', "headerFilter": "input", "headerFilterPlaceholder": "Search version..."},
            {'field': 'cve', 'title': 'CVE', "headerFilter": "input", "headerFilterPlaceholder": "Search CVE..."},
            {'field': 'cvss3', 'title': 'CVSS', "headerFilter": "input", "headerFilterPlaceholder": "Search CVSS..."},
            {'field': 'cvss3_score', 'title': 'CVSS rating', "headerFilter": "input", "headerFilterPlaceholder": "Search score..."},
            {'field': 'link', 'title': 'Exploit/POC URL', "headerFilter": "input", "headerFilterPlaceholder": "Search exploit..."},
            {'field': 'cve_url', 'title': 'CVE URL', "headerFilter": "input", "headerFilterPlaceholder": "Search CVE URL..."},
            {'field': 'vulnerability_type', 'title': 'Vulnerability type', "headerFilter": "input", "headerFilterPlaceholder": "Search type..."},
        ]



