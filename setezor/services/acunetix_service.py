import asyncio
import csv
import datetime
import io

import json
from fastapi import HTTPException, UploadFile
from setezor.schemas.acunetix.schemes.group import GroupForm, GroupMembershipSet
from setezor.schemas.acunetix.schemes.report import ReportAddForm
from setezor.schemas.acunetix.schemes.scan import GroupScanStart, TargetScanStart
from setezor.schemas.acunetix.schemes.target import SyncPayload, TargetToSync
from setezor.schemas.acunetix.schemes.target_config import ScanSpeedValues
from setezor import managers as M
from setezor.tools.websocket_manager import WS_MANAGER
from setezor.models import Acunetix
from setezor.services.base_service import BaseService
from setezor.models.d_software import Software
from setezor.models.domain import Domain
from setezor.models.ip import IP
from setezor.models.l4_software import L4Software
from setezor.models.l4_software_vulnerability import L4SoftwareVulnerability
from setezor.models.port import Port
from setezor.models.task import Task
from setezor.models import Scan
from setezor.modules.acunetix.target import Target
from setezor.modules.acunetix.vulnerability import Vulnerability
from setezor.modules.acunetix.acunetix import AcunetixApi
from setezor.restructors.dns_scan_task_restructor import DNS_Scan_Task_Restructor
from setezor.schemas.task import WebSocketMessage
from setezor.data_writer.data_structure_service import DataStructureService
from setezor.tasks.acunetix_scan_task import AcunetixScanTask
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.modules.acunetix.acunetix_config import Config
from setezor.modules.osint.dns_info.dns_info import DNS as DNSModule
from setezor.models import Vulnerability as VulnerabilityModel
from setezor.models.dns_a import DNS_A
from setezor.tools.url_parser import parse_url

class AcunetixService:
    @classmethod
    async def get_project_apis(cls, uow: UnitOfWork, project_id: str) -> list[Acunetix]:
        async with uow:
            apis = await uow.acunetix.filter(project_id=project_id)
            return apis

    @classmethod
    async def add_config(cls, uow: UnitOfWork, project_id: str, config: Acunetix) -> int:
        result = await Config.health_check(config.model_dump())
        if result.get("code"):
            raise HTTPException(status_code=500)
        config.project_id = project_id
        config_dict = config.model_dump()
        async with uow:
            if (await uow.acunetix.find_one(project_id=project_id, url=config.url)):
                raise HTTPException(status_code=500, detail=f"Acunetix with url={config.url} is already registered")
            new_config = uow.acunetix.add(config_dict)
            await uow.commit()

        # api = AcunetixApi.from_config(new_config.model_dump())
        # targets = await api.get_targets()
        # print(targets)
        # result = await cls.parse_targets(targets)
        # ds = DataStructureService(uow=uow, result=result, scan_id=None, project_id=project_id)
        # await ds.make_magic()
        return new_config

    @classmethod
    async def parse_targets(cls, targets):
        result = []
        ips = {}
        for target in targets:
            data = parse_url(url=target["address"])
            scheme = target["address"].split("://")[0]
            if domain := data.get("domain"):
                responses = [await DNSModule.resolve_domain(domain, "A")]
                domains = DNSModule.proceed_records(responses)
                new_domain, new_ip, dns_a = await DNS_Scan_Task_Restructor.restruct(domains, domain)
                if new_ip.ip in ips:
                    new_ip = ips[new_ip.ip]
                    dns_a.ip = new_ip
                else:
                    ips[new_ip.ip] = new_ip
                result.extend([new_domain, new_ip, dns_a])
            else:
                new_domain = Domain(domain="")
                result.append(new_domain)

            if ip := data.get("ip"):
                new_ip = IP(ip=ip)
                if new_ip.ip in ips:
                    new_ip = ips[new_ip.ip]
                else:
                    ips[new_ip.ip] = new_ip
                result.append(new_ip)


            if port := data.get("port"):
                new_port = Port(port=port, ip=new_ip)
                result.append(new_port)
            else:
                if scheme == "https":
                    new_port = Port(port=443, ip=new_ip)
                else:
                    new_port = Port(port=80, ip=new_ip)
                result.append(new_port)
        return result

    @classmethod
    async def get_groups(cls, uow: UnitOfWork, project_id: str, acunetix_id: int = None):
        if acunetix_id:
            async with uow:
                config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
                api = AcunetixApi.from_config(config.model_dump())
                return await api.get_groups()
        groups = []
        async with uow:
            configs = await uow.acunetix.filter(project_id=project_id)
            for config in configs:
                api = AcunetixApi.from_config(config.model_dump())
                groups.extend(await api.get_groups())
            return groups
        
    @classmethod
    async def add_group(cls, uow: UnitOfWork, project_id: str, form: GroupForm, acunetix_id: int):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            status, msg = await api.add_group(form.model_dump_json())
            return status, json.dumps(msg)
        
    @classmethod
    async def get_group_targets(cls, uow: UnitOfWork, group_id: str, project_id: str, acunetix_id: int):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            resp = await api.get_group_targets(group_id=group_id)
            targets_ids = resp['target_id_list']
            tasks = []
            for target_id in targets_ids:
                task = asyncio.create_task(api.get_target_by_id(target_id=target_id))
                tasks.append(task)
            targets = await asyncio.gather(*tasks)
            return targets
        
    @classmethod
    async def set_group_targets(cls, uow: UnitOfWork, group_id: str, project_id: str, acunetix_id: int, payload: GroupMembershipSet):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            return await api.set_group_targets(group_id=group_id, payload=payload.model_dump())

    @classmethod
    async def set_group_targets_proxy(cls, uow: UnitOfWork, group_id: str, project_id: str, acunetix_id: int, payload: dict):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            return await api.set_group_targets_proxy(group_id=group_id, payload=payload)

    @classmethod
    def get_scans_speeds(cls):
        return [s.value for s in ScanSpeedValues]
    
    @classmethod
    async def get_scanning_profiles(cls, uow: UnitOfWork, project_id: str):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id)
            api = AcunetixApi.from_config(config.model_dump())
            return await api.get_scanning_profiles()
        

    @classmethod
    async def get_targets(cls, uow: UnitOfWork, project_id: str, acunetix_id: int = None):
        targets = []
        async with uow:
            if acunetix_id:
                config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
                api = AcunetixApi.from_config(config.model_dump())
                targets = await api.get_targets()
            else:
                configs = await uow.acunetix.filter(project_id=project_id)
                for config in configs:
                    api = AcunetixApi.from_config(config.model_dump())
                    targets.extend(await api.get_targets())
        return targets
        
    @classmethod
    async def get_targets_for_sync(cls, uow: UnitOfWork, project_id: str, acunetix_id: str):
        targets = await cls.get_targets(uow=uow, project_id=project_id, acunetix_id=acunetix_id)
        groups = await cls.get_groups(uow=uow, project_id=project_id, acunetix_id=acunetix_id)
        target_to_group = {}
        output = {"deadbeef": {"name": "No group",
                               "targets": []
                               }}
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            for group in groups:
                resp = await api.get_group_targets(group_id=group["group_id"])
                targets_ids = resp['target_id_list']
                for target in targets_ids:
                    target_to_group[target] = group["group_id"]
                output[group["group_id"]] = {"name": group["name"],
                                             "targets": []
                                             }
        for target in targets:
            data = parse_url(url=target["address"])
            scheme = target["address"].split("://")[0]
            async with uow:
                target_in_setezor = await uow.target.find_one(protocol=scheme, project_id=project_id, **data)
            target["in_setezor_id"] = target_in_setezor.id if target_in_setezor else None
            if group_id := target_to_group.get(target["target_id"]):
                output[group_id]["targets"].append(target)
            else:
                output["deadbeef"]["targets"].append(target)
        return output

    @classmethod
    async def sync_targets_between_setezor_and_acunetix(cls, uow: UnitOfWork, sync_payload: SyncPayload, scan_id: str, project_id: str):
        ips = {}
        ports = {}
        common_domains = {}
        result = []
        empty_domains = {}
        empty_dns = {}
        found_dns = {}
        async with uow:
            for index, target in enumerate(sync_payload.targets):
                scope_id = target.scope_id
                acunetix_id = target.acunetix_id
                acunetix_target_id = target.in_acunetix_id

                data = parse_url(url=target.address)
                scheme = target.address.split("://")[0]

                if target.in_setezor_id:
                    target_in_setezor = await uow.target.find_one(project_id=project_id, id=target.in_setezor_id)
                else:
                    target_in_setezor = await uow.target.find_one(project_id=project_id,
                                                                  protocol=scheme,
                                                                  scope_id=scope_id,
                                                                  **data)
                    if not target_in_setezor:
                        target_in_setezor = uow.target.add({
                            "project_id": project_id,
                            "protocol": scheme,
                            "scope_id": scope_id,
                            **data
                        })
                        await uow.commit()

                config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
                api = AcunetixApi.from_config(config.model_dump())

                if domain := data.get("domain"):
                    if domain in common_domains:
                        new_domain = common_domains[domain]
                        new_dns_a = found_dns[domain]
                    else:
                        try:
                            responses = [await DNSModule.resolve_domain(domain=domain, record="A")]
                            domains = DNSModule.proceed_records(responses)
                            new_domain, new_ip, new_dns_a = await DNS_Scan_Task_Restructor.restruct(domains, domain) # может не разрезолвить
                            if new_ip.ip in ips and new_ip.ip:
                                new_ip = ips[new_ip.ip]
                                new_dns_a.target_ip = new_ip
                                result.append(new_dns_a)
                            else:
                                ips[new_ip.ip] = new_ip
                                result.append(new_ip)
                                result.append(new_dns_a)
                        except:
                            new_domain = Domain(domain=domain)
                            new_ip = IP()
                            new_dns_a = DNS_A(target_ip=new_ip, target_domain=new_domain)
                            result.append(new_ip)
                            result.append(new_dns_a)
                        
                        common_domains[domain] = new_domain
                        found_dns[domain] = new_dns_a
                        result.append(new_domain)

                if ip := data.get("ip"):
                    if ip in ips:
                        new_ip = ips[ip]
                        if not (ip in empty_domains):
                            new_domain = Domain()
                            result.append(new_domain)
                            new_dns_a = DNS_A(target_ip=new_ip, target_domain=new_domain)
                            result.append(new_dns_a)
                            empty_domains[ip] = new_domain
                            empty_dns[ip] = new_dns_a
                        new_domain = empty_domains[ip]
                        new_dns_a = empty_dns[ip]
                    else:
                        new_ip = IP(ip=ip)
                        ips[ip] = new_ip
                        result.append(new_ip)
                        
                        new_domain = Domain()
                        result.append(new_domain)
                        
                        new_dns_a = DNS_A(target_ip=new_ip, target_domain=new_domain)
                        result.append(new_dns_a)
                        empty_domains[ip] = new_domain
                        empty_dns[ip] = new_dns_a


                key = f"{new_ip.ip or new_domain.domain}_{data.get("port")}"
                if key in ports:
                    new_port =  ports[key]
                else:
                    new_port = Port(port=data.get("port"), ip=new_ip)
                    ports[key] = new_port
                    result.append(new_port)


                new_software = Software()
                result.append(new_software)

                new_l4_software = L4Software(l4=new_port, dns_a=new_dns_a, software=new_software)
                result.append(new_l4_software)

                scans = await api.get_target_scans(target_id=acunetix_target_id)
                for scan in scans:
                    start_datetime = datetime.datetime.fromisoformat(scan["current_session"]["start_date"])
                    if start_datetime.date() >= sync_payload.dt_from and start_datetime.date() <= sync_payload.dt_to:
                        last_scan_id = scan["scan_id"]
                        last_scan_result_id = scan["current_session"]["scan_session_id"]
                        break
                else:
                    continue
                
                vulnerabilities = await api.get_scan_vulnerabilities(scan_id=last_scan_id, result_id=last_scan_result_id)
                scan_result_statistic = await api.get_scan_result_statistic(scan_id=last_scan_id, result_id=last_scan_result_id)
                end_date = datetime.datetime.fromisoformat(scan_result_statistic["scanning_app"]["wvs"]["end_date"])
                if not len(vulnerabilities):
                    continue

                vulnerabilities = Vulnerability.from_acunetix_response(vulnerabilities)
                for vuln in vulnerabilities:
                    vuln_obj = VulnerabilityModel(created_at_in_acunetix=end_date, **vuln)
                    l4_software_vuln = L4SoftwareVulnerability(l4_software=new_l4_software, vulnerability=vuln_obj)
                    result.append(vuln_obj)
                    result.append(l4_software_vuln)

                message = WebSocketMessage(title="Import", text=f"{index + 1} / {len(sync_payload.targets)}",type="info")
                await WS_MANAGER.send_message(project_id=project_id, message=message)


            ds = DataStructureService(uow=uow)
            await ds.make_magic(result=result, project_id=project_id, scan_id=scan_id)

    @classmethod
    async def add_targets(cls, uow: UnitOfWork, project_id: str, acunetix_id: int, payload: dict):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            status, msg, result = await api.add_target(payload=payload)
            result = await cls.parse_targets(result)
            ds = DataStructureService(uow=uow)
            await ds.make_magic(result=result, project_id=project_id, scan_id=None)
            return status
    
    @classmethod
    async def delete_target(cls, uow: UnitOfWork, project_id: str, acunetix_id:int, target_id: str):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            return await api.delete_target(target_id=target_id)
    
    @classmethod
    async def import_targets_from_csv(cls, uow: UnitOfWork, project_id: str, acunetix_id:int, group_id: str, targets_csv: UploadFile):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            data = csv.reader(io.StringIO(targets_csv.file.read().decode()))
            raw_payload = {
                "group_id": group_id
            }
            for index, line in enumerate(data):
                addr = line[0]
                raw_payload[f"address{index+1}"] = addr
                raw_payload[f"description{index+1}"] = addr
            status, msg, result = await api.add_target(payload=raw_payload)
            result = await cls.parse_targets(result)
            ds = DataStructureService(uow=uow)
            await ds.make_magic(result=result, scan_id=None, project_id=project_id)
            return 204 if status == 200 else 500



    @classmethod
    async def set_target_proxy(cls, uow: UnitOfWork, project_id: str, target_id: str, payload:dict, acunetix_id: int):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            return await api.set_target_proxy(target_id=target_id, payload=payload)
        
    @classmethod
    async def set_target_cookies(cls, uow: UnitOfWork, project_id: str, target_id: str, payload:dict, acunetix_id: int):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            return await api.set_target_cookies(target_id=target_id, payload=payload)
    
    @classmethod
    async def set_target_headers(cls, uow: UnitOfWork, project_id: str, target_id: str, payload:dict, acunetix_id: int):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            return await api.set_target_headers(target_id=target_id, payload=payload)

    @classmethod
    async def get_reports(cls, uow: UnitOfWork, project_id: str, acunetix_id: int = None):
        if acunetix_id:
            async with uow:
                config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
                api = AcunetixApi.from_config(config.model_dump())
                return await api.get_reports()
        reports = []
        async with uow:
            configs = await uow.acunetix.filter(project_id=project_id)
            for config in configs:
                api = AcunetixApi.from_config(config.model_dump())
                reports.extend(await api.get_reports())
            return reports
        
    @classmethod
    async def create_report(cls, uow: UnitOfWork, project_id: str, acunetix_id: int, create_report_form: ReportAddForm):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
            return await api.create_report(payload=create_report_form.model_dump())
        
    @classmethod
    async def get_report_file(cls, uow: UnitOfWork, project_id: str, report_id: str, format:str, acunetix_id: int):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
        
        filename, data, status = await api.get_report_file(report_id=report_id, extension=format)
        return filename, data
    
    @classmethod
    async def get_report_templates(cls, uow: UnitOfWork, project_id: str):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id)
            api = AcunetixApi.from_config(config.model_dump())
            return await api.get_report_templates()
        
    @classmethod
    async def get_scans(cls, uow: UnitOfWork, project_id: str, acunetix_id: int = None):
        if acunetix_id:
            async with uow:
                config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
                api = AcunetixApi.from_config(config.model_dump())
                return await api.get_scans()
        scans = []
        async with uow:
            configs = await uow.acunetix.filter(project_id=project_id)
            for config in configs:
                api = AcunetixApi.from_config(config.model_dump())
                scans.extend(await api.get_scans())
            return scans
        

    @classmethod
    async def create_scan(cls, uow: UnitOfWork, project_id: str, acunetix_id: int, scan_id: str, form: TargetScanStart | GroupScanStart):
        async with uow:
            config = await uow.acunetix.find_one(project_id=project_id, id=acunetix_id)
            api = AcunetixApi.from_config(config.model_dump())
        if hasattr(form, 'group_id'):
            raw_data = await api.create_scan_for_group(payload=form.model_dump())
        if hasattr(form, 'target_id'):
            raw_data = await api.create_scan_for_target(payload=form.model_dump())
        for _, scan in raw_data:
            target_id = scan.get("target_id")
            target = await api.get_target_by_id(target_id=target_id)
            target_address = target.get("address")
            acunetix_scan_id = scan.get("scan_id")
            task: Task = await M.TaskManager.create_local_job(
                job=AcunetixScanTask,
                agent_id = None,
                uow=uow,
                project_id=project_id,
                target_address=target_address,
                credentials=api.credentials,
                scan_id=scan_id,
                acunetix_scan_id=acunetix_scan_id
            )
        return True