import io
import json
import os
import struct
import zipfile

from setezor.clients.base_api_client import ApiClient, File, GetAs
from setezor.models import Task
from setezor.modules.site_parser.screenshoter import ScreenshotModule
from setezor.modules.site_parser.wappalyzer import WappalyzerModule
from setezor.modules.site_parser.web_archive import WebArchiveModule
from setezor.restructors.parse_site_restructor import ParseSiteTaskRestructor
from setezor.schemas.task import TaskLog
from setezor.settings import PATH_PREFIX
from setezor.tasks.base_job import BaseJob
from setezor.models.target import Target


class ParseSiteTask(BaseJob):
    restructor = ParseSiteTaskRestructor
    folders = ['web_archives', 'wappalyzer_logs', 'screenshots']

    @classmethod
    def get_task_logs(cls, task: Task, **kwargs) -> list[TaskLog]:
        logs_list = []
        for folder in cls.folders:
            file_path = os.path.join(PATH_PREFIX, 'projects', task.project_id, task.scan_id, folder)
            if not os.path.exists(file_path):
                continue

            if folder == 'web_archives':
                f_data = f'/api/v1/web_archives/{task.id}'
                file_name = WebArchiveModule.get_file_name_by_task_id(
                    project_id=task.project_id, scan_id=task.scan_id, task_id=task.id
                )
            elif folder == 'wappalyzer_logs':
                file_name = WappalyzerModule.get_file_name_by_task_id(
                    project_id=task.project_id, scan_id=task.scan_id, task_id=task.id
                )
                with open(os.path.join(file_path, file_name), 'r') as f:
                    f_data = json.load(f)

            elif folder == 'screenshots':
                f_data = f'/api/v1/dns_a_screenshot/screenshot/{task.id}'
                file_name = ScreenshotModule.get_file_name_by_task_id(
                    project_id=task.project_id, scan_id=task.scan_id, task_id=task.id
                )
            else:
                continue

            logs_list.append(TaskLog(type=folder, file_name=file_name, file_data=f_data))

        return logs_list

    @classmethod
    async def download_browser(cls, module_path: str, browser_version: str, platform_name: str):
        browser_file: File = await ApiClient().get(
            f'https://storage.googleapis.com/chrome-for-testing-public/{browser_version}/{platform_name}/'
            f'chrome-{platform_name}.zip',
            get_as=GetAs.file
        )
        with zipfile.ZipFile(io.BytesIO(browser_file.content), 'r') as zip_ref:
            zip_ref.extractall(module_path)

        os.rename(os.path.join(module_path, f'chrome-{platform_name}'),
                  os.path.join(module_path, 'browser'))

    @classmethod
    async def download_wappalyzer(cls, module_path: str, browser_version: str):
        wappalyzer_file: File = await ApiClient().get(
            f'https://clients2.google.com/service/update2/crx?response=redirect&prodversion='
            f'{browser_version}&acceptformat=crx2,crx3&x=id%3Dgppongmhjkpfnbhagpmjfkannfbllamg%26uc',
            get_as=GetAs.file
        )
        stream = io.BytesIO(wappalyzer_file.content)

        stream.read(4)
        version = struct.unpack('<I', stream.read(4))[0]

        if version == 2:
            pub_len = struct.unpack('<I', stream.read(4))[0]
            sig_len = struct.unpack('<I', stream.read(4))[0]
            stream.seek(pub_len + sig_len, io.SEEK_CUR)
        elif version == 3:
            header_len = struct.unpack('<I', stream.read(4))[0]
            stream.seek(header_len, io.SEEK_CUR)
        else:
            raise ValueError(f"Unsupported CRX version: {version}")

        with zipfile.ZipFile(stream) as z:
            z.extractall(os.path.join(module_path, 'wappalyzer'))

    @classmethod
    async def prepare_module(cls, module_path: str, agent_info: dict, *args, **kwargs):
        browser_version = cls.get_browser_version(module_path)
        payload = agent_info.get('tasks', {}).get(cls.__name__, {}).get('payload')
        if payload:
            platform_name = payload['platform_name']
            await cls.download_browser(module_path, browser_version, platform_name)
            await cls.download_wappalyzer(module_path, browser_version)

    @classmethod
    def get_browser_version(cls, module_path: str) -> str | None:
        path = os.path.join(module_path, 'external', 'playwright', 'driver', 'package', 'browsers.json')
        data = json.load(open(path, 'r'))
        for browser in data['browsers']:
            browser_name = browser['name']
            if browser_name == 'chromium':
                return browser['browserVersion']
            
    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        params = []
        for t in targets:
            addresses = []
            if t.ip:
                addresses.append(t.ip.split('/')[0].strip())
            if t.domain:
                addresses.append(t.domain.strip())
            
            for addr in addresses:
                port_val = str(t.port).strip() if t.port else None
                
                if port_val == '80':
                    params.append({**base_kwargs, "url": f"http://{addr}:80"})
                elif port_val == '443':
                    params.append({**base_kwargs, "url": f"https://{addr}:443"})
                else:
                    http_port = port_val if port_val else '80'
                    https_port = port_val if port_val else '443'
                    params.append({**base_kwargs, "url": f"http://{addr}:{http_port}"})
                    params.append({**base_kwargs, "url": f"https://{addr}:{https_port}"})
        return params