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


    async def get_device_types(self, project_id: str) -> Dict:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            result = await self._uow.object.get_most_frequent_values_device_type(project_id=project_id, last_scan_id=last_scan_id)
            device_types = [{"labels": row[0], "data": row[1]} for row in result]
            return {
                "data": [item["data"] for item in device_types],
                "labels": [item["labels"] for item in device_types]
            }


    async def get_object_count(self, project_id: str) -> int:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            return await self._uow.object.get_object_count(project_id=project_id, last_scan_id=last_scan_id)


    async def get_ip_count(self, project_id: str) -> int:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            return await self._uow.ip.get_ip_count(project_id=project_id, last_scan_id=last_scan_id)


    async def get_mac_count(self, project_id: str) -> int:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            return await self._uow.mac.get_mac_count(project_id=project_id, last_scan_id=last_scan_id)


    async def get_port_count(self, project_id: str) -> int:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            return await self._uow.port.get_port_count(project_id=project_id, last_scan_id=last_scan_id)

    async def get_software_version_cpe(self, project_id: str) -> Dict:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            result = await self._uow.software.get_software_version_cpe(project_id=project_id, last_scan_id=last_scan_id)
            return {
                'product': [i[0] for i in result],
                'version': [i[1] for i in result],
                'cpe23': [i[2] for i in result],
                'data': [i[3] for i in result]
            }

    async def get_top_products(self, project_id: str) -> List:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            return await self._uow.software.get_top_products(project_id=project_id, last_scan_id=last_scan_id)

    async def get_top_ports(self, project_id: str) -> List:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            return await self._uow.port.get_top_ports(project_id=project_id, last_scan_id=last_scan_id)

    async def get_top_protocols(self, project_id: str) -> List:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            return await self._uow.port.get_top_protocols(project_id=project_id, last_scan_id=last_scan_id)

    async def get_vulnerabilities(self, project_id: str) -> Dict:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            result = await self._uow.vulnerability.get_vulnerabilities(project_id=project_id, last_scan_id=last_scan_id)
            return {
                'name': [i[0] for i in result],
                'cve': [i[1] for i in result],
                'description': [i[2] for i in result],
                'cvss_score': [i[3] for i in result]
            }

    async def get_ports_and_protocols(self, project_id: str) -> Dict:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            result = await self._uow.l4_software.get_ports_and_protocols(project_id=project_id, last_scan_id=last_scan_id)
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

    async def get_products_and_service_name(self, project_id: str) -> Dict:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            result = await self._uow.l4_software.get_product_service_name_info_from_sunburts(project_id=project_id, last_scan_id=last_scan_id)
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
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            total, rows = await self._uow.l4_software.get_l4_software_tabulator_data(
                project_id=project_id,
                last_scan_id=last_scan_id,
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
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            total, tabulator_dashboard_data = await self._uow.ip.get_ip_mac_port_data(
                project_id=project_id,
                last_scan_id=last_scan_id,
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
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            total, tabulator_dashboard_data = await self._uow.ip.get_domain_ip_data(
                project_id=project_id,
                last_scan_id=last_scan_id,
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
            })

        return total, tabulator_transform_dashboard_data

    async def get_l4_soft_vuln_link_tabulator_data(
        self, 
        project_id: str, 
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
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            total, rows = await self._uow.l4_software.get_soft_vuln_link_data(
                project_id=project_id,
                last_scan_id=last_scan_id,
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
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            total, data = await self._uow.authentication_credentials.get_data_for_tabulator(
                project_id=project_id,
                last_scan_id=last_scan_id,
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

    async def get_ip_tabulator_data(self, project_id: str) -> list:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            tabulator_dashboard_data = await self._uow.ip.get_ip_data(project_id=project_id, last_scan_id=last_scan_id)
            keys = [
            "id",
            "ipaddr", 
            "mac", 
            ]

            tabulator_transform_dashboard_data = [
                dict(zip(keys, row)) for row in tabulator_dashboard_data
            ]
            return tabulator_transform_dashboard_data

    async def get_mac_tabulator_data(self, project_id: str) -> list:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            tabulator_dashboard_data = await self._uow.mac.get_mac_tabulator_data(project_id=project_id, last_scan_id=last_scan_id)
            keys = [
            "id",
            "object", 
            "mac", 
            "vendor", 
            ]

            tabulator_transform_dashboard_data = [
                dict(zip(keys, row)) for row in tabulator_dashboard_data
            ]
            return tabulator_transform_dashboard_data

    async def get_port_tabulator_data(self, project_id: str) -> list:
        async with self._uow:
            last_scan_id = await self.get_last_scan_id(project_id=project_id)
            tabulator_dashboard_data = await self._uow.port.get_port_tabulator_data(project_id=project_id, last_scan_id = last_scan_id)
            keys = [
            "id",
            "ipaddr", 
            "port",
            "protocol",
            "service_name",
            ]
            tabulator_transform_dashboard_data = [
                dict(zip(keys, row)) for row in tabulator_dashboard_data
            ]
            return tabulator_transform_dashboard_data



    @classmethod
    def get_l4_software_columns_tabulator_data(cls) -> list:
        return [{'field': 'id', 'title': 'ID'},
                    {'field': 'ipaddr', 'title': 'IP'},
                    {'field': 'domain', 'title': 'DOMAIN'},
                    {'field': 'port', 'title': 'PORT'},
                    {'field': 'state', 'title': 'STATE'},
                    {'field': 'protocol', 'title': 'PROTOCOL'},
                    {'field': 'service_name', 'title': 'SERVICE_NAME'},
                    {'field': 'vendor', 'title': 'VENDOR'},
                    {'field': 'product', 'title': 'PRODUCT'},
                    {'field': 'version', 'title': 'VERSION'},
                #  {'field': 'type', 'title': 'TYPE'},
                #  {'field': 'build', 'title': 'BUILD'},
                #  {'field': 'patch', 'title': 'PATCH'},
                #  {'field': 'platform', 'title': 'PLATFORM'},
                #  {'field': 'cpe23', 'title': 'CPE23'}
                ]

    @classmethod
    def get_ip_mac_port_columns_tabulator_data(cls) -> list:
        return [{'field': 'id', 'title': 'ID'},
                    {'field': 'ipaddr', 'title': 'IP'},
                    {'field': 'port', 'title': 'PORT'},
                    {'field': 'mac', 'title': 'MAC'}]

    @classmethod
    def get_domain_ip_columns_tabulator_data(cls) -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'ipaddr', 'title': 'IP'},
                {'field': 'port', 'title': 'PORT'},
                {'field': 'domain', 'title': 'DOMAIN'},
                ]


    @classmethod
    def get_soft_vuln_link_columns_tabulator_data(cls) -> list:
        return [{'field': 'vendor', 'title': 'VENDOR'},
                       {'field': 'product', 'title': 'PRODUCT'},
                       {'field': 'type', 'title': 'TYPE'},
                       {'field': 'version', 'title': 'VERSION'},
                       {'field': 'build', 'title': 'BUILD'},
                       {'field': 'patch', 'title': 'PATCH'},
                       {'field': 'platform', 'title': 'PLATFORM'},
                       {'field': 'cpe23', 'title': 'CPE23'},
                       {'field': 'vulnerability_name', 'title': 'VULN_NAME'},
                       {'field': 'cve', 'title': 'CVE'},
                       {'field': 'cwe', 'title': 'CWE'},
                       {'field': 'link', 'title': 'LINK'}]

    @classmethod
    def get_auth_credentials_tabulator_data(cls) -> list:
        return [       {'field': 'id', 'title': 'ID'},
                       {'field': 'ipaddr', 'title': 'IP'},
                       {'field': 'domain', 'title': 'DOMAIN'},
                       {'field': 'port', 'title': 'PORT'},
                       {'field': 'login', 'title': 'LOGIN'},
                       {'field': 'password', 'title': 'PASSWORD'},
                       {'field': 'permissions', 'title': 'PERMISSIONS'},
                       {'field': 'parameters', 'title': 'PARAMETERS'}]
    # @classmethod
    # def get_ip_columns_tabulator_data(cls) -> list:
    #     return [{'field': 'id', 'title': 'ID'},
    #                    {'field': 'mac','title': 'MAC',},
    #                    {'field': 'ipaddr','title': 'IP',}]


    # @classmethod
    # def get_mac_columns_tabulator_data(cls) -> list:
    #     return [{'field': 'id', 'title': 'ID'},
    #                    {'field': 'object', 'title': 'Object',},
    #                    {'field': 'mac', 'title': 'MAC',},
    #                    {'field': 'vendor', 'title': 'Vendor',}]


    # @classmethod
    # def get_port_columns_tabulator_data(cls) -> list:
    #     return [{'field': 'id', 'title': 'ID'},
    #                    {'field': 'ipaddr','title': 'IP',},
    #                    {'field': 'port','title': 'Port',},
    #                    {'field': 'protocol','title': 'Protocol',},
    #                    {'field': 'service_name','title': 'Service name'}]


