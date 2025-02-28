import pprint
import uuid
import json
from typing import Dict
from setezor.unit_of_work import UnitOfWork
import orjson


class AnalyticsService:
    
    @classmethod
    def restruct_result(cls, data: list, column1: str, column2: str, field_count: str):
        if data:
            labels = []
            parents = []
            graph_values = []
            node_graph_values = {}

            for item in data:
                col1_value = str(item.get(column1, ''))
                col2_value = str(item.get(column2, '')).upper()
                count = item.get(field_count, 0)

                if col2_value and col2_value not in node_graph_values:
                    labels.append(col2_value)
                    parents.append('')
                    node_graph_values[col2_value] = 0

                if col1_value:
                    labels.append(col1_value)
                    parents.append(col2_value)
                    node_graph_values[col1_value] = count

                if col2_value:
                    node_graph_values[col2_value] += count

            for label in labels:
                graph_values.append(node_graph_values.get(label, 0))

            return {
                'labels': orjson.dumps(labels).decode(),
                'parents': orjson.dumps(parents).decode(),
                'graph_values': orjson.dumps(graph_values).decode()
            }
        else:
            return {
                'labels': '[]',
                'parents': '[]',
                'graph_values': '[]'
            }

    # TODO
    '''Класс для получения данных из whois сделанный перед нг, потом его нужно будет запихнуть куда нибудь в нормальное место'''
    @classmethod
    async def get_whois_data(cls, uow: UnitOfWork, project_id: uuid.UUID) -> Dict:
        async with uow:
            whois_ip_data = await uow.whois_ip.get_whois_ip_data(project_id=project_id)
            whois__transform_ip_data = {
                    'domain_crt': [i[0] for i in whois_ip_data],
                    'netname': [json.loads(i[1]).get('netname') for i in whois_ip_data],
                    'data': [i[1] for i in whois_ip_data],
                    'AS': [i[2] for i in whois_ip_data],
                    'range_ip': [i[3] for i in whois_ip_data],
            }
            whois_domain_data = await uow.whois_domain.get_whois_domain_data(project_id=project_id)
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

    @classmethod
    async def get_all_analytics(cls, uow: UnitOfWork, project_id: str) -> Dict:
        async with uow:
            ports_software_result = await uow.L7Software.get_ports_software_info(project_id=project_id)
            ports_software_info = [row._asdict() for row in ports_software_result]

            products_service_name_result = await uow.L7Software.get_product_service_name_info(project_id=project_id)
            products_service_name = [row._asdict() for row in products_service_name_result]

            device_types_result = await uow.object.get_most_frequent_values_device_type(project_id=project_id)
            device_types = [{"labels": row[0], "data": row[1]} for row in device_types_result]
            device_types_transform_data = {
                "data": [item["data"] for item in device_types],
                "labels": [item["labels"] for item in device_types]
            }

            object_count = await uow.object.get_object_count(project_id=project_id)
            ip_count = await uow.ip.get_ip_count(project_id=project_id)
            mac_count = await uow.mac.get_mac_count(project_id=project_id)
            port_count = await uow.port.get_port_count(project_id=project_id)

            software_version_cpe = await uow.software.get_software_version_cpe(project_id=project_id)
            software_version_cpe_transform_data = {
                'product': [i[0] for i in software_version_cpe],
                'version': [i[1] for i in software_version_cpe],
                'cpe23': [i[2] for i in software_version_cpe],
                'data': [i[3] for i in software_version_cpe]
            }

            top_products = await uow.software.get_top_products(project_id=project_id)
            top_ports = await uow.port.get_top_ports(project_id=project_id)
            top_protocols = await uow.port.get_top_protocols(project_id=project_id)

            vulnerabilities = await uow.vulnerability.get_vulnerabilities(project_id=project_id)
            vulnerabilities_transform_data = {
                'name': [i[0] for i in vulnerabilities],
                'cve': [i[1] for i in vulnerabilities],
                'description': [i[2] for i in vulnerabilities],
                'cvss_score': [i[3] for i in vulnerabilities]
            }


            ports_and_protocols_result = await uow.L7Software.get_ports_and_protocols(project_id=project_id)
            labels = []
            parents = []
            graph_values = []
            for label, parent, value in ports_and_protocols_result:
                labels.append(label)
                parents.append(parent)
                graph_values.append(value)
            top_ports_and_protocols  = {"labels" : orjson.dumps(labels).decode(),
                                        "parents" : orjson.dumps(parents).decode(),
                                        "graph_values" : orjson.dumps(graph_values).decode()}
            
            products_service_name_result_from_sunburst = await uow.L7Software.get_product_service_name_info_from_sunburts(project_id=project_id)
            labels = []
            parents = []
            graph_values = []
            for label, parent, value in products_service_name_result_from_sunburst:
                if parent:
                    labels.append(label)
                else:
                    labels.append(label.capitalize())
                parents.append(parent.capitalize())
                graph_values.append(value)
            top_products_and_servise_name  = {"labels" : orjson.dumps(labels).decode(),
                                        "parents" : orjson.dumps(parents).decode(),
                                        "graph_values" : orjson.dumps(graph_values).decode()}
                

            context = {
                'ports_software_info': ports_software_info,
                'products_service_name': products_service_name,
                'object_count': object_count,
                'ip_count': ip_count,
                'mac_count': mac_count,
                'port_count': port_count,
                'device_types': device_types_transform_data,
                'software_version_cpe': software_version_cpe_transform_data,
                'top_ports': top_ports,
                'top_protocols': top_protocols,
                'top_products': top_products,
                'vulnerabilities': vulnerabilities_transform_data,
                'top_ports_and_protocols': top_ports_and_protocols,
                'top_products_and_servise_name': top_products_and_servise_name,
            }
            return context
        
    @classmethod
    async def get_l7_software_tabulator_data(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
        
            tabulator_dashboard_data = await uow.L7Software.get_resource_software_tabulator_data(project_id=project_id)
            keys = [
            "id",
            "ipaddr", 
            "port", 
            "protocol", 
            "service_name", 
            "domain", 
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
                dict(zip(keys, row)) for row in tabulator_dashboard_data
            ]
            return tabulator_transform_dashboard_data
    
    @classmethod
    async def get_l4_software_tabulator_data(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
        
            tabulator_dashboard_data = await uow.l4_software.get_l4_software_tabulator_data(project_id=project_id)
            keys = [
            "id",
            "ipaddr", 
            "port", 
            "protocol", 
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
                dict(zip(keys, row)) for row in tabulator_dashboard_data
            ]
            return tabulator_transform_dashboard_data
        
    @classmethod
    async def get_ip_mac_port_tabulator_data(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
        
            tabulator_dashboard_data = await uow.ip.get_ip_mac_port_data(project_id=project_id)
            keys = [
            "id",
            "ipaddr", 
            "port", 
            "mac"
            ]

            tabulator_transform_dashboard_data = [
                dict(zip(keys, row)) for row in tabulator_dashboard_data
            ]
            return tabulator_transform_dashboard_data
        
    @classmethod
    async def get_domain_ip_tabulator_data(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
        
            tabulator_dashboard_data = await uow.ip.get_domain_ip_data(project_id=project_id)
            keys = [
            "ipaddr", 
            "port", 
            "domain", 
            ]

            tabulator_transform_dashboard_data = [
                dict(zip(keys, row)) for row in tabulator_dashboard_data
            ]
            return tabulator_transform_dashboard_data
        
    @classmethod
    async def get_l7_soft_vuln_link_tabulator_data(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
        
            tabulator_dashboard_data = await uow.L7Software.get_soft_vuln_link_data(project_id=project_id)
            keys = [
            "id",
            "vendor", 
            "product", 
            "type", 
            "version", 
            "build", 
            "patch", 
            "platform", 
            "cpe23", 
            "name", 
            "cve", 
            "cwe", 
            "link", 
            ]

            tabulator_transform_dashboard_data = [
                dict(zip(keys, row)) for row in tabulator_dashboard_data
            ]
            return tabulator_transform_dashboard_data
        
    @classmethod
    async def get_l4_soft_vuln_link_tabulator_data(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
        
            tabulator_dashboard_data = await uow.l4_software.get_soft_vuln_link_data(project_id=project_id)
            keys = [
            "vendor", 
            "product", 
            "type", 
            "version", 
            "build", 
            "patch", 
            "platform", 
            "cpe23", 
            "name", 
            "cve", 
            "cwe", 
            "link", 
            ]

            tabulator_transform_dashboard_data = [
                dict(zip(keys, row)) for row in tabulator_dashboard_data
            ]
            return tabulator_transform_dashboard_data
        
    @classmethod
    async def get_ip_tabulator_data(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
        
            tabulator_dashboard_data = await uow.ip.get_ip_data(project_id=project_id)
            keys = [
            "id",
            "ipaddr", 
            "mac", 
            ]

            tabulator_transform_dashboard_data = [
                dict(zip(keys, row)) for row in tabulator_dashboard_data
            ]
            return tabulator_transform_dashboard_data
        
    @classmethod
    async def get_mac_tabulator_data(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
        
            tabulator_dashboard_data = await uow.mac.get_mac_tabulator_data(project_id=project_id)
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

    @classmethod
    async def get_port_tabulator_data(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
        
            tabulator_dashboard_data = await uow.port.get_port_tabulator_data(project_id=project_id)
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
    async def get_l7_credentials(cls, uow: UnitOfWork, project_id: str) -> list:
        result = []
        async with uow:
            data = await uow.l7_authentication_credentials.get_data_for_tabulator(project_id=project_id)
        for id, item in enumerate(data, 1):
            ip, domain, port, auth = item
            result.append({
                    "id" : id,
                    "ip" : ip.ip,
                    "domain" : domain.domain,
                    "port" : port.port,
                    "login" : auth.login,
                    "passwords" : auth.password,
                    "permissions" : ("no permissions", "read", "write", "read/write")[auth.permissions],
                    "parameters" : auth.parameters })
        return result

    @classmethod
    def get_l7_software_columns_tabulator_data(cls) -> list:
        return [{'field': 'id', 'title': 'ID'},
                    {'field': 'ipaddr', 'title': 'IP'},
                    {'field': 'port', 'title': 'PORT'},
                    {'field': 'protocol', 'title': 'PROTOCOL'},
                    {'field': 'service_name', 'title': 'SERVICE_NAME'},
                    {'field': 'domain', 'title': 'DOMAIN'},
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
    def get_l4_software_columns_tabulator_data(cls) -> list:
        return [{'field': 'id', 'title': 'ID'},
                    {'field': 'ipaddr', 'title': 'IP'},
                    {'field': 'port', 'title': 'PORT'},
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
        return [{'field': 'ipaddr', 'title': 'IP'},
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
                       {'field': 'name', 'title': 'VULN_NAME'},
                       {'field': 'cve', 'title': 'CVE'},
                       {'field': 'cwe', 'title': 'CWE'},
                       {'field': 'link', 'title': 'LINK'}]
        
    @classmethod
    def get_l7_credentials_tabulator_data(cls) -> list:
        return [       {'field': 'id', 'title': 'ID'},
                       {'field': 'ip', 'title': 'IP'},
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

        
