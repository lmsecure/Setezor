import uuid
import json
from typing import Dict, List, Optional
from setezor.services.base_service import BaseService
from setezor.unit_of_work import UnitOfWork
import orjson
from datetime import datetime

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


    async def get_ip_info_tabulator_data(
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
            total, ip_info_data = await self._uow.ip.get_ip_info_tabulator_data(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params,
                filter_params=filter_params
            )
        tabulator_transform_ip_info_data = []
        for index, row in enumerate(ip_info_data, start=(page - 1) * size + 1):
            ipaddr, start_ip, mask, AS_name, AS_number, org_name = row
            tabulator_transform_ip_info_data.append({
                "id": index,
                "ipaddr": ipaddr,
                "range_ip": f"{start_ip}/{mask}",
                "AS": AS_name,
                "AS-number": AS_number,
                "org-name": org_name
            })
        return total, tabulator_transform_ip_info_data
    

    async def get_domain_info_tabulator_data(
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
            total, domain_info_data = await self._uow.ip.get_domain_info_tabulator_data(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params,
                filter_params=filter_params
            )
        tabulator_transform_domain_info_data = []
        for index, row in enumerate(domain_info_data, start=(page - 1) * size + 1):
            domain, org_name, data_json = row
            
            try:
                data = json.loads(data_json) if isinstance(data_json, str) else data_json
            except:
                data = {}

            domain_name = data.get("ldhName", domain)

            entities = data.get("entities", {})
            registrant = entities.get("registrant", [])
            organization, address, country, email, phone = "", "", "", "", ""
            contact_str = ""

            if registrant:
                first = registrant[0]
                
                org = first.get("org", "")
                name_dict = first.get("name", {})
                name = ""
                if isinstance(name_dict, dict):
                    name = name_dict.get("default") or name_dict.get("en") or name_dict.get("ru", "")
                elif isinstance(name_dict, str):
                    name = name_dict

                organization = org or name
                if not organization.strip():
                    organization = "Organization hidden"

                taxpayer_id = first.get("taxpayer_id", "")
                if taxpayer_id:
                    organization += f" (ИНН: {taxpayer_id})"

                address = first.get("address", "")
                country = first.get("country", "")
                email = first.get("email", "")
                phone = first.get("phone", "")

                contact_info = []
                if email:
                    contact_info.append(f"Email: {email}")
                if phone:
                    contact_info.append(f"Phone: {phone}")
                if address or country:
                    addr = f"{address}, {country}".strip(", ")
                    contact_info.append(f"Address: {addr}")
                contact_str = "; ".join(contact_info) if contact_info else "Contact information hidden"
            
            def safe_parse_date(date_str):
                if not date_str:
                    return ""
                try:
                    dt = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00")
                                .replace(" ", "T")
                    )
                    return dt.strftime("%Y-%m-%d")
                except:
                    return str(date_str)
                
            created = safe_parse_date(data.get("registration"))
            expires = safe_parse_date(data.get("expiration") or data.get("registrar_expiration"))

            nameservers_list = []
            if isinstance(data.get("nameservers"), list):
                nameservers_list = [
                    ns.get("ldhName", "") for ns in data["nameservers"]
                    if isinstance(ns, dict) and ns.get("ldhName")
                ]
            nameservers_str = ", ".join(nameservers_list)

            record = {
                "id": index,
                "domain": domain_name,
                "org-name": organization,
                "country": country,
                "contacts": contact_str if contact_str else "",
                "created": created,
                "expires": expires,
                "nameservers": nameservers_str,
                "data": data_json
            }
            tabulator_transform_domain_info_data.append(record)

        return total, tabulator_transform_domain_info_data


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

            vulns = await self._uow.vulnerability.get_count_vulns_by_port_ids(
                project_id=project_id, port_ids=port_ids, scans=scans
            )
            
            tabulator_transform_web_data = []

            for index, row in enumerate(rows, start=(page - 1) * size + 1):
                port_id = row[5]
                port_links = all_links.get(port_id, [])
                vulns_count = vulns.get(port_id, 0)
                links_str = ", ".join(port_links) if port_links else ""

                row_data = {
                    "id": index,
                    "ipaddr": row[0],
                    "domain": row[1],
                    "port": row[2],
                    "product": row[3],
                    "vulns_count": vulns_count,
                    "ip_id": row[4],
                    "port_id": row[5],
                    "link": links_str,
                    "comments_count": row[6]
                }

                tabulator_transform_web_data.append(row_data)

            return total, tabulator_transform_web_data

    async def get_web_archives_tabulator_data(
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
            total, rows = await self._uow.web_archive.get_web_archive_data(
                project_id=project_id,
                scans=scans,
                page=page,
                size=size,
                sort_params=sort_params or [],
                filter_params=filter_params or [])
        keys = ["id", "archive_id", "domain", "url"]
        tabulator = [
            dict(zip(keys, [i] + list(row))) for i, row in enumerate(rows, 1)
        ]
        return total, tabulator

        
    @classmethod
    def get_l4_software_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'port', 'title': 'PORT', "headerFilter": "number", "headerFilterPlaceholder": "Search port..."},
            {'field': 'state', 'title': 'STATE', "headerFilter": "input", "headerFilterPlaceholder": "Search state..."},
            {'field': 'protocol', 'title': 'PROTOCOL', "headerFilter": "input", "headerFilterPlaceholder": "Search protocol..."},
            {'field': 'service_name', 'title': 'SERVICE_NAME', "headerFilter": "input", "headerFilterPlaceholder": "Search service..."},
            {'field': 'vendor', 'title': 'VENDOR', "headerFilter": "input", "headerFilterPlaceholder": "Search vendor..."},
            {'field': 'product', 'title': 'PRODUCT', "headerFilter": "input", "headerFilterPlaceholder": "Search product..."},
            {'field': 'version', 'title': 'VERSION', "headerFilter": "input", "headerFilterPlaceholder": "Search version..."},
            {'field': 'os', 'title': 'OS', "headerFilter": "input", "headerFilterPlaceholder": "Search OS..."},
            {'field': 'is_secured', 'title': 'is_secured', "headerFilter":"select", "headerFilterPlaceholder": "Select true/false", 'headerFilterParams': {'values': [True, False]}},
        ]

    # @classmethod
    # def get_ip_mac_port_columns_tabulator_data(cls) -> list:
    #     return [
    #         {'field': 'id', 'title': 'ID'},
    #         {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
    #         {'field': 'port', 'title': 'PORT', "headerFilter": "number", "headerFilterPlaceholder": "Search port..."},
    #         {'field': 'mac', 'title': 'MAC', "headerFilter": "input", "headerFilterPlaceholder": "Search MAC..."},
    #     ]
    
    # @classmethod
    # def get_domain_ip_columns_tabulator_data(cls) -> list:
    #     return [
    #         {'field': 'id', 'title': 'ID'},
    #         {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
    #         {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
    #         {'field': 'DNS', 'title': 'DNS', "headerFilter": "input", "headerFilterPlaceholder": "Search DNS..."},
    #         {'field': 'value', 'title': 'VALUE', "headerFilter": "input", "headerFilterPlaceholder": "Search value..."},
    #         {'field': 'extra_data', 'title': 'EXTRA DATA', "headerFilter": "input", "headerFilterPlaceholder": "Search extra data..."},
    #         {'field': 'comments', 'title': 'Comments'},
    #     ]


    # @classmethod
    # def get_soft_vuln_link_columns_tabulator_data(cls) -> list:
    #     return [
    #         {'field': 'vendor', 'title': 'VENDOR', "headerFilter": "input", "headerFilterPlaceholder": "Search vendor..."},
    #         {'field': 'product', 'title': 'PRODUCT', "headerFilter": "input", "headerFilterPlaceholder": "Search product..."},
    #         {'field': 'type', 'title': 'TYPE', "headerFilter": "input", "headerFilterPlaceholder": "Search type..."},
    #         {'field': 'version', 'title': 'VERSION', "headerFilter": "input", "headerFilterPlaceholder": "Search version..."},
    #         {'field': 'build', 'title': 'BUILD', "headerFilter": "input", "headerFilterPlaceholder": "Search build..."},
    #         {'field': 'cpe23', 'title': 'CPE23', "headerFilter": "input", "headerFilterPlaceholder": "Search CPE..."},
    #         {'field': 'vulnerability_name', 'title': 'VULN_NAME', "headerFilter": "input", "headerFilterPlaceholder": "Search vuln name..."},
    #         {'field': 'cve', 'title': 'CVE', "headerFilter": "input", "headerFilterPlaceholder": "Search CVE..."},
    #         {'field': 'cwe', 'title': 'CWE', "headerFilter": "input", "headerFilterPlaceholder": "Search CWE..."},
    #         {'field': 'link', 'title': 'LINK', "headerFilter": "input", "headerFilterPlaceholder": "Search link..."},
    #     ]

    # @classmethod
    # def get_auth_credentials_tabulator_data(cls) -> list:
    #     return [
    #         {'field': 'id', 'title': 'ID'},
    #         {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
    #         {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
    #         {'field': 'port', 'title': 'PORT', "headerFilter": "number", "headerFilterPlaceholder": "Search port..."},
    #         {'field': 'login', 'title': 'LOGIN', "headerFilter": "input", "headerFilterPlaceholder": "Search login..."},
    #         {'field': 'password', 'title': 'PASSWORD', "headerFilter": "input", "headerFilterPlaceholder": "Search password..."},
    #         {'field': 'permissions', 'title': 'PERMISSIONS', "headerFilter": "number", "headerFilterPlaceholder": "Search permissions..."},
    #         {'field': 'parameters', 'title': 'PARAMETERS', "headerFilter": "input", "headerFilterPlaceholder": "Search parameters..."},
    #     ]
    
    # @classmethod
    # def get_dns_a_screenshot_columns_tabulator_data(cls) -> list:
    #     return [
    #         {'field': 'id', 'title': 'ID'},
    #         {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
    #         {'field': 'ip', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
    #         {'field': 'screenshot_path', 'title': 'SCREENSHOT_PATH'},
    #         {'field': 'created_at', 'title': 'CREATED_AT', "headerFilter": "input", "headerFilterPlaceholder": "Search date..."},
    #     ]

    # # Пинтестеры

    # @classmethod
    # def get_whois_columns_tabulator_data(cls) -> list:
    #     return [
    #         {'field': 'id', 'title': 'ID'},
    #         {'field': 'ipaddr', 'title': 'WHOIS IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
    #         {'field': 'domain', 'title': 'WHOIS Domain', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
    #         {'field': 'range_ip', 'title': 'Range IP', "headerFilter": "input", "headerFilterPlaceholder": "Search range..."},
    #         {'field': 'AS', 'title': 'AS', "headerFilter": "input", "headerFilterPlaceholder": "Search AS..."},
    #         {'field': 'org-name', 'title': 'Org-name', "headerFilter": "input", "headerFilterPlaceholder": "Search org..."},
    #         {'field': 'data', 'title': 'Data', "headerFilter": "input", "headerFilterPlaceholder": "Search data..."},
    #     ]
    
    # @classmethod
    # def get_web_columns_tabulator_data(cls) -> list:
    #     return [
    #         {'field': 'id', 'title': 'ID'},
    #         {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
    #         {'field': 'domain', 'title': 'Domain', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
    #         {'field': 'port', 'title': 'Ports', "headerFilter": "number", "headerFilterPlaceholder": "Search ports..."},
    #         {'field': 'code', 'title': 'Code', "headerFilter": "input", "headerFilterPlaceholder": "Search code..."},
    #         {'field': 'product', 'title': 'Software', "headerFilter": "input", "headerFilterPlaceholder": "Search software..."},
    #         {'field': 'waf', 'title': 'WAF', "headerFilter": "input", "headerFilterPlaceholder": "Search WAF..."},
    #         {'field': 'is_vuln_scanned', 'title': 'Is vuln scanned', "headerFilter":"select", "headerFilterPlaceholder": "Select true/false", 'headerFilterParams': {'values': [True, False]}},
    #         {'field': 'link', 'title': 'Vuln and exploits'},
    #         {'field': 'comments', 'title': 'Comments'},
    #     ]
    
    # @classmethod
    # def get_api_columns_tabulator_data(cls) -> list:
    #     return [
    #         {'field': 'id', 'title': 'ID'},
    #         {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
    #         {'field': 'domain', 'title': 'Domain', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
    #         {'field': 'api_dir', 'title': 'API Dir', "headerFilter": "input", "headerFilterPlaceholder": "Search dir..."},
    #         {'field': 'api_endpoint', 'title': 'API Endpoint', "headerFilter": "input", "headerFilterPlaceholder": "Search endpoint..."},
    #         {'field': 'http_method', 'title': 'HTTP Method', "headerFilter": "input", "headerFilterPlaceholder": "GET/POST..."},
    #         {'field': 'body', 'title': 'body', "headerFilter": "input", "headerFilterPlaceholder": "Search body..."},
    #         {'field': 'comments', 'title': 'Comments'},
    #     ]
    
    # @classmethod
    # def get_cve_columns_tabulator_data(cls) -> list:
    #     return [
    #         {'field': 'id', 'title': 'ID'},
    #         {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
    #         {'field': 'product', 'title': 'Software', "headerFilter": "input", "headerFilterPlaceholder": "Search software..."},
    #         {'field': 'version', 'title': 'Version', "headerFilter": "input", "headerFilterPlaceholder": "Search version..."},
    #         {'field': 'cve', 'title': 'CVE', "headerFilter": "input", "headerFilterPlaceholder": "Search CVE..."},
    #         {'field': 'cvss3', 'title': 'CVSS', "headerFilter": "input", "headerFilterPlaceholder": "Search CVSS..."},
    #         {'field': 'cvss3_score', 'title': 'CVSS rating', "headerFilter": "input", "headerFilterPlaceholder": "Search score..."},
    #         {'field': 'link', 'title': 'Exploit/POC URL', "headerFilter": "input", "headerFilterPlaceholder": "Search exploit..."},
    #         {'field': 'cve_url', 'title': 'CVE URL', "headerFilter": "input", "headerFilterPlaceholder": "Search CVE URL..."},
    #         {'field': 'vulnerability_type', 'title': 'Vulnerability type', "headerFilter": "input", "headerFilterPlaceholder": "Search type..."},
    #     ]
    
    @classmethod
    def get_ip_info_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID','width': 100},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'range_ip', 'title': 'Range IP'},
            {'field': 'AS', 'title': 'AS', "headerFilter": "input", "headerFilterPlaceholder": "Search AS..."},
            {'field': 'AS-number', 'title': 'AS number', "headerFilter": "input", "headerFilterPlaceholder": "Search AS number..."},
            {'field': 'org-name', 'title': 'Org-name', "headerFilter": "input", "headerFilterPlaceholder": "Search org..."}
        ]
    
    @classmethod
    def get_domain_info_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID','width': 100},
            {'field': 'domain', 'title': 'Domain', "headerFilter": "input", "headerFilterPlaceholder": "Search domain...",'width': 160, 'tooltip': True},
            {'field': 'contacts', 'title': 'Contacts', 'tooltip': True},
            {'field': 'org-name', 'title': 'Org-name', 'tooltip': True},
            {'field': 'country', 'title': 'Country','width': 140},
            {'field': 'created', 'title': 'Created','width': 150},
            {'field': 'expires', 'title': 'Expires','width': 150},
            {'field': 'nameservers', 'title': 'Nameservers', 'tooltip': True},
            {'field': 'data', 'title': 'Data','width': 140},
        ]
    
    @classmethod
    def get_open_ports_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID','width': 100},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'os', 'title': 'OS', "headerFilter": "input", "headerFilterPlaceholder": "Search OS..."},
            {'field': 'port', 'title': 'PORT', "headerFilter": "number", "headerFilterPlaceholder": "Search port..."},
            {'field': 'protocol', 'title': 'PROTOCOL', "headerFilter": "input", "headerFilterPlaceholder": "Search protocol..."},
            {'field': 'service_name', 'title': 'SERVICE_NAME', "headerFilter": "input", "headerFilterPlaceholder": "Search service..."},
            {'field': 'ttl', 'title': 'ttl'},
            {'field': 'vendor', 'title': 'VENDOR', "headerFilter": "input", "headerFilterPlaceholder": "Search vendor..."},
            {'field': 'product', 'title': 'PRODUCT', "headerFilter": "input", "headerFilterPlaceholder": "Search product..."},
            {'field': 'version', 'title': 'VERSION', "headerFilter": "input", "headerFilterPlaceholder": "Search version..."},    
            {'field': 'vulns_btn', 'title': 'Vulnerabilities'},
        ]
    
    @classmethod
    def get_ip_domain_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID','width': 100},
            {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'DNS', 'title': 'DNS', "headerFilter": "input", "headerFilterPlaceholder": "Search DNS..."},
            {'field': 'value', 'title': 'VALUE', "headerFilter": "input", "headerFilterPlaceholder": "Search value..."},
            {'field': 'extra_data', 'title': 'EXTRA_DATA', "headerFilter": "input", "headerFilterPlaceholder": "Search extra data...", "tooltip": 'true'}
        ]
    
    @classmethod
    def get_web_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID','width': 100},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'domain', 'title': 'Domain', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'port', 'title': 'Ports', "headerFilter": "number", "headerFilterPlaceholder": "Search ports..."},
            {'field': 'code', 'title': 'Code', "headerFilter": "input", "headerFilterPlaceholder": "Search code..."},
            {'field': 'dirb', 'title': 'dirb'},
            {'field': 'product', 'title': 'Software', "headerFilter": "input", "headerFilterPlaceholder": "Search software..."},
            {'field': 'waf', 'title': 'WAF', "headerFilter": "input", "headerFilterPlaceholder": "Search WAF..."},
            {'field': 'is_vuln_scanned', 'title': 'Is vuln scanned', "headerFilter":"select", "headerFilterPlaceholder": "Select true/false", 'headerFilterParams': {'values': [True, False]}},
            {'field': 'vulns_btn', 'title': 'Vulnerabilities'},
            {'field': 'comments', 'title': 'Comments'},
        ]

    @classmethod
    def get_web_screenshot_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID','width': 100},
            {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'ip', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'screenshot_path', 'title': 'SCREENSHOT'},
            {'field': 'created_at', 'title': 'CREATED_AT', "headerFilter": "input", "headerFilterPlaceholder": "Search date..."}
        ]

    @classmethod
    def get_cve_columns_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID','width': 100},
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
    
    @classmethod
    def get_auth_credentials_tabulator_data(cls) -> list:
        return [
            {'field': 'id', 'title': 'ID','width': 100},
            {'field': 'ipaddr', 'title': 'IP', "headerFilter": "input", "headerFilterPlaceholder": "Search IP..."},
            {'field': 'domain', 'title': 'DOMAIN', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'port', 'title': 'PORT', "headerFilter": "number", "headerFilterPlaceholder": "Search port..."},
            {'field': 'login', 'title': 'LOGIN', "headerFilter": "input", "headerFilterPlaceholder": "Search login..."},
            {'field': 'password', 'title': 'PASSWORD', "headerFilter": "input", "headerFilterPlaceholder": "Search password..."},
            {'field': 'permissions', 'title': 'PERMISSIONS', "headerFilter": "number", "headerFilterPlaceholder": "Search permissions..."},
            {'field': 'parameters', 'title': 'PARAMETERS', "headerFilter": "input", "headerFilterPlaceholder": "Search parameters..."},
        ]

    @classmethod
    def web_archive_headers(cls) -> list:
        return [
            {'field': 'archive_id', 'title': 'ID','width': 100},
            {'field': 'domain', 'title': 'Domain', "headerFilter": "input", "headerFilterPlaceholder": "Search domain..."},
            {'field': 'url', 'title': 'Url', "headerFilter": "input", "headerFilterPlaceholder": "Search url..."}
        ]