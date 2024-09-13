import aiofiles
import json
from .acunetix import AcunetixApi


class AcunetixManager:
    """
        Класс управления окунями
    """

    def __init__(self, config_path: str, apis: dict[str, AcunetixApi]):
        self.config_path = config_path
        self._apis = apis

    @classmethod
    def load_acunetix_apis(cls, path: str):
        with open(path, 'r') as file:
            configs = json.load(file)
        return cls(config_path=path, apis={name: AcunetixApi.from_config(name=name, config=config)
                                           for name, config in configs.items()})

    @property
    def apis(self):
        return [value.__dict__ for value in self._apis.values()]

    def get_credentials(self, name):
        return self._apis[name].credentials

    def add_api(self, data):
        with open(self.config_path, 'r') as file:
            current_instances = json.load(file)
        name, config = data.pop("name"), data
        self._apis[name] = AcunetixApi.from_config(name=name, config=config)
        current_instances[name] = config
        with open(self.config_path, 'w') as file:
            file.write(json.dumps(current_instances, indent=4))

    async def get_targets(self, name: str | None = None):
        if name:
            return await self._apis[name].get_targets()
        targets = []
        for api in self._apis.values():
            targets.extend(await api.get_targets())
        return targets

    async def get_target_by_id(self, name: str, target_id: str):
        return await self._apis[name].get_target_by_id(target_id=target_id)

    async def add_target(self, name: str, payload):
        return await self._apis[name].add_target(payload)

    async def delete_target(self, name: str, target_id: str):
        return await self._apis[name].delete_target(target_id=target_id)

    async def set_target_proxy(self, name: str, target_id: str, payload):
        return await self._apis[name].set_target_proxy(target_id=target_id, payload=payload)

    async def set_target_cookies(self, name: str, target_id: str, payload):
        return await self._apis[name].set_target_cookies(target_id=target_id, payload=payload)

    async def set_target_headers(self, name: str, target_id: str, payload):
        return await self._apis[name].set_target_headers(target_id=target_id, payload=payload)

    async def get_groups(self, name: str | None = None):
        if name:
            return await self._apis[name].get_groups()
        groups = []
        for api in self._apis.values():
            groups.extend(await api.get_groups())
        return groups

    async def add_group(self, name: str, payload):
        return await self._apis[name].add_group(payload)

    async def get_group_targets(self, name: str, group_id: str):
        return await self._apis[name].get_group_targets(group_id=group_id)

    async def set_group_targets(self, name: str, group_id: str, payload):
        return await self._apis[name].set_group_targets(group_id=group_id, payload=payload)

    async def set_group_targets_proxy(self, name: str, group_id: str, payload):
        return await self._apis[name].set_group_targets_proxy(group_id=group_id, payload=payload)

    async def get_scans(self, name: str | None = None):
        if name:
            return await self._apis[name].get_scans()
        scans = []
        for api in self._apis.values():
            scans.extend(await api.get_scans())
        return scans

    async def create_scan_for_group(self, name: str, payload):
        return await self._apis[name].create_scan_for_group(payload=payload)

    async def create_scan_for_target(self, name: str, payload):
        return await self._apis[name].create_scan_for_target(payload=payload)

    async def create_scan_for_db_obj(self, name: str, payload):
        return await self._apis[name].create_scan_for_db_obj(payload=payload)

    async def get_reports(self, name: str):
        if name:
            return await self._apis[name].get_reports()
        reports = []
        for api in self._apis.values():
            reports.extend(await api.get_reports())
        return reports

    async def create_report(self, name: str, payload):
        return await self._apis[name].create_report(payload=payload)

    async def get_report_file(self, name: str, report_id: str, extension: str):
        return await self._apis[name].get_report_file(report_id=report_id, extension=extension)

    async def get_scanning_profiles(self):
        for api in self._apis.values():
            return await api.get_scanning_profiles()

    async def get_report_templates(self):
        for api in self._apis.values():
            return await api.get_report_templates()
