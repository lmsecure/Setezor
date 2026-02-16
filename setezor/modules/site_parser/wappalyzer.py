import json
import os
from datetime import datetime

from setezor.settings import PROJECTS_DIR_PATH


class WappalyzerModule:

    @classmethod
    def save(cls, wappalyzer_data: dict, task_id: str, project_id: str, scan_id: str, **kwargs) -> dict:
        filename = f"{str(datetime.now())}_ParseSiteTask_{task_id}"
        logs_path = os.path.join(PROJECTS_DIR_PATH, project_id, scan_id, 'wappalyzer_logs')
        os.makedirs(logs_path, exist_ok=True)
        json.dump(
            wappalyzer_data,
            open(os.path.join(logs_path, f'{filename}.json'), 'w')
        )
        return {'name': filename}

    @classmethod
    def prepare_wappalyzer_data(cls, wappalyzer_data: list[dict], url: str) -> dict:
        result = {
            'urls': {url: ''},
            'technologies': []
        }
        for item in wappalyzer_data:
            result['technologies'].append(item)

        return result

    @classmethod
    def get_file_name_by_task_id(cls, project_id: str, scan_id: str, task_id: str) -> str:
        logs_path = os.path.join(PROJECTS_DIR_PATH, project_id, scan_id, 'wappalyzer_logs')
        os.makedirs(logs_path, exist_ok=True)
        for file in os.listdir(logs_path):
            if task_id in file:
                return file
