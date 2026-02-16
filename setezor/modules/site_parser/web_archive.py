import base64
import gzip
import os
import io
import json
from datetime import datetime
from setezor.tools.url_parser import parse_url

import socket
import aiofiles

from har2warc.har2warc import har2warc

from setezor.db.entities import DNSTypes
from setezor.models import DNS, Domain, IP
from setezor.models.web_archive import WebArchive
from setezor.settings import PROJECTS_DIR_PATH
from setezor.tools.zip_files_manager import Base64


class WebArchiveModule:

    @classmethod
    def _har_to_warc(cls, har: bytes) -> bytes:
        har_json = json.loads(har.decode())
        for entry in har_json["log"]["entries"]:
            content = entry["response"].get("content", {})
            if content.get("encoding") == "base64" and "text" in content:
                content["text"] = base64.b64decode(content["text"]).decode("utf-8", errors="ignore")
                content.pop("encoding", None)

        output = io.BytesIO()
        har2warc(har_json, output)
        output.seek(0)
        return output.getvalue()

    @classmethod
    async def parse(cls, har: Base64, task_id: str, project_id: str, scan_id: str, **kwargs) -> dict:
        har = base64.b64decode(har)
        warc_gz = cls._har_to_warc(har)
        warc = gzip.decompress(warc_gz)
        filename = f"{str(datetime.now())}_ParseSiteTask_{task_id}.warc"
        archives_path = os.path.join(PROJECTS_DIR_PATH, project_id, scan_id, 'web_archives')
        if not os.path.exists(archives_path):
            os.makedirs(archives_path, exist_ok=True)
        file_path = os.path.join(archives_path, filename)
        async with aiofiles.open(file_path, 'wb') as file:
            await file.write(warc)
        return {'name': filename}
    
    @classmethod
    def _resolve_ip(cls, domain: str) -> str: # FixMe change to DNSModule.resolve_domain(domain, "A")
        """Резолвит IP адрес домена"""
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror:
            return "0.0.0.0" # пиздец зашквар

    @classmethod
    async def restruct_result(cls, url: str, name: str, dns_obj: DNS):
        web_archive_obj = WebArchive(name=name, dns=dns_obj, url=url)
        return [web_archive_obj]


    @classmethod
    def get_file_name_by_task_id(cls, project_id: str, scan_id: str, task_id: str) -> str:
        logs_path = os.path.join(PROJECTS_DIR_PATH, project_id, scan_id, 'web_archives')
        os.makedirs(logs_path, exist_ok=True)
        for file in os.listdir(logs_path):
            if task_id in file:
                return file
