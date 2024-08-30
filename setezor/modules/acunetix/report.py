from .utils import send_request
import datetime
import json


class Report:

    url = "/api/v1/reports"

    @classmethod
    async def get_all(cls, params: dict, credentials: dict):
        raw_data = await send_request(base_url=credentials["url"],
                                      token=credentials["token"],
                                      url=cls.url,
                                      method="GET",
                                      params=params)
        if raw_data.get("code"):
            return {}
        reports: list[Report] = raw_data.get("reports")
        for report in reports:
            raw_datetime = datetime.datetime.strptime(
                report['generation_date'], "%Y-%m-%dT%H:%M:%S.%f%z")
            raw_datetime = raw_datetime + \
                datetime.datetime.now().astimezone().tzinfo.utcoffset(datetime.datetime.now())
            report['generation_date'] = datetime.datetime.strftime(
                raw_datetime, "%d.%m.%Y, %H:%M:%S")
        pagination = raw_data.get("pagination")
        count = pagination.get("count")
        return reports, count

    @classmethod
    async def create(cls, payload: dict, credentials: dict):
        raw_data = {
            "template_id": payload["template_id"],
            "source": {
                "list_type": "scans",
                "id_list": [
                    payload["scan_id"]
                ]
            }
        }
        data = json.dumps(raw_data, indent=4)
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=cls.url,
                                  method="POST",
                                  data=data)

    @classmethod
    async def download(cls, id: str, extension: str, credentials: dict):
        report = await send_request(base_url=credentials["url"],
                                    token=credentials["token"],
                                    url=f"{cls.url}/{id}",
                                    method="GET")
        download_links = report.get("download")
        if not download_links:
            return "", "", 500
        download_link = None
        for link in report.get("download", []):
            if link.endswith(extension):
                download_link = link
                break
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=download_link,
                                  method="GET")

    @classmethod
    async def get_templates(cls,credentials: dict):
        result = await send_request(base_url=credentials["url"],
                                    token=credentials["token"],
                                    url="/api/v1/report_templates",
                                    method="GET")
        return result.get("templates", {})
