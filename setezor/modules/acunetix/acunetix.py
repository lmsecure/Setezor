from setezor.modules.acunetix.target import Target
from setezor.modules.acunetix.group import Group
from setezor.modules.acunetix.scan import Scan
from setezor.modules.acunetix.report import Report
from setezor.modules.acunetix.vulnerability import Vulnerability

class AcunetixApi:
    def __init__(self, id: int, name: str, url: str, token: str, offset: str):
        self.id = id
        self.name = name
        self.url = url
        self.token = token
        self.offset = offset

    @classmethod
    def from_config(cls, config):
        return cls(id=config.get("id"), name=config["name"], url=config["url"], token=config["token"], offset=config["offset"])

    @property
    def credentials(self):
        return {
            "url": self.url,
            "token": self.token,
            "timeUTCOffset": self.offset
        }

    async def get_targets(self):
        result = await Target.get_all(credentials=self.credentials)
        for target in result:
            target["acunetix_id"] = self.id
            target["acunetix_name"] = self.name
        return result

    async def add_target(self, payload: dict):
        result = []
        for i in range(len(payload) // 2):
            raw_payload = {
                "address": payload[f"address{i+1}"],
                "description": payload[f"description{i+1}"],
                "group_id": payload["group_id"]
            }
            status, msg = await Target.create(payload=raw_payload, credentials=self.credentials)
            raw_payload["target_id"] = msg["targets"][0]["target_id"]
            result.append(raw_payload)
        return status, msg, result
    
    async def delete_target(self, target_id: str):
        return await Target.delete(id=target_id, credentials=self.credentials)

    async def get_target_by_id(self, target_id: str):
        return await Target.get_by_id(id=target_id, credentials=self.credentials)
    
    async def get_target_scans(self, target_id: str):
        return await Target.get_target_scans(id=target_id, credentials=self.credentials)

    async def set_target_proxy(self, target_id: str, payload):
        return await Target.set_proxy(id=target_id, payload=payload, credentials=self.credentials)

    async def set_target_cookies(self, target_id: str, payload):
        return await Target.set_cookies(id=target_id, payload=payload, credentials=self.credentials)

    async def set_target_headers(self, target_id: str, payload):
        return await Target.set_headers(id=target_id, payload=payload, credentials=self.credentials)

    async def get_groups(self):
        result = await Group.get_all(credentials=self.credentials)
        for group in result:
            group["acunetix_id"] = self.id
            group["acunetix_name"] = self.name
        return result

    async def add_group(self, payload):
        return await Group.create(payload=payload, credentials=self.credentials)

    async def get_group_targets(self, group_id: str):
        return await Group.get_targets(id=group_id, credentials=self.credentials)

    async def set_group_targets(self, group_id: str, payload):
        return await Group.set_targets(id=group_id, payload=payload, credentials=self.credentials)

    async def set_group_targets_proxy(self, group_id: str, payload):
        return await Group.set_targets_proxy(id=group_id, payload=payload, credentials=self.credentials)

    async def get_scans(self):
        result = await Scan.get_all(credentials=self.credentials)
        for scan in result:
            scan["acunetix_id"] = self.id
            scan["acunetix_name"] = self.name
        return result

    async def get_scan_vulnerabilities(self, scan_id: str, result_id: str):
        vulnerabilities = await Scan.get_vulnerabilities(id=scan_id, result_id=result_id, credentials=self.credentials)
        for vulnerability in vulnerabilities:
            detail = await Vulnerability.get_by_id(id=vulnerability["target_vuln_id"], credentials=self.credentials)
            http_response = await Vulnerability.get_http_response(vulnerability_id=vulnerability["vuln_id"], 
                                                                  scan_id=scan_id,
                                                                  result_id=result_id,
                                                                  credentials=self.credentials)
            vulnerability |= detail
            vulnerability["response"] = http_response
        return vulnerabilities

    async def get_scan_result_statistic(self, scan_id: str, result_id: str):
        return await Scan.get_statistics(scan_id=scan_id, result_id=result_id, credentials=self.credentials)

    async def create_scan_for_group(self, payload):
        return await Scan.create_for_group(payload=payload, credentials=self.credentials)

    async def create_scan_for_target(self, payload):
        return await Scan.create_for_target(payload=payload, credentials=self.credentials)

    async def create_scan_for_db_obj(self, payload):
        return await Scan.create_for_db_obj(payload=payload, credentials=self.credentials)

    async def get_scanning_profiles(self):
        return await Scan.get_profiles(credentials=self.credentials)

    async def get_reports(self):
        result = await Report.get_all(credentials=self.credentials)
        for report in result:
            report["acunetix_id"] = self.id
            report["acunetix_name"] = self.name
        return result

    async def create_report(self, payload):
        return await Report.create(payload=payload, credentials=self.credentials)

    async def get_report_file(self, report_id: str, extension: str):
        return await Report.download(id=report_id, extension=extension, credentials=self.credentials)

    async def get_report_templates(self):
        return await Report.templates(credentials=self.credentials)
