import base64
import socket
from datetime import datetime
from setezor.tools.url_parser import parse_url

import aiofiles
import os

from setezor.db.entities import DNSTypes
from setezor.models import DNS, DNS_A_Screenshot, Domain, IP
from setezor.settings import PROJECTS_DIR_PATH
from setezor.tools.zip_files_manager import Base64


class ScreenshotModule:

    @classmethod
    async def parse(cls, screenshot: Base64, project_id: str, scan_id: str, task_id: str, **kwargs) -> dict:
        screenshots_path = os.path.join(PROJECTS_DIR_PATH, project_id, scan_id, 'screenshots')
        if not os.path.exists(screenshots_path):
            os.makedirs(screenshots_path, exist_ok=True)

        filename = f"{str(datetime.now())}_ParseSiteTask_{task_id}"
        file_path = os.path.join(screenshots_path, filename)
        screenshot = base64.b64decode(screenshot)
        async with aiofiles.open(file_path, 'wb') as file:
            await file.write(screenshot)

        return {
            'screenshot_id': task_id,
        }

    @classmethod
    async def restruct_result(cls, screenshot_id: str, dns_obj: DNS):
        dns_a_screenshot = DNS_A_Screenshot(dns=dns_obj, screenshot_id=screenshot_id)
        return [dns_a_screenshot]

    @classmethod
    def get_file_name_by_task_id(cls, project_id: str, scan_id: str, task_id: str) -> str:
        logs_path = os.path.join(PROJECTS_DIR_PATH, project_id, scan_id, 'screenshots')
        os.makedirs(logs_path, exist_ok=True)
        for file in os.listdir(logs_path):
            if task_id in file:
                return file
