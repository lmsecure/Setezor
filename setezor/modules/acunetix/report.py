from .utils import send_request, parse_utc_offset
import datetime
import json


class Report:

    url = "/api/v1/reports"

    @classmethod
    async def get_all(cls, credentials: dict):
        params = {"l": 100, "c": 0}
        raw_data = await send_request(base_url=credentials["url"],
                                      token=credentials["token"],
                                      url=cls.url,
                                      method="GET",
                                      params=params)
        if raw_data.get("code"):
            return {}
        reports: list[Report] = raw_data.get("reports")
        while True:
            params["c"] += 100
            raw_data = await send_request(base_url=credentials["url"],
                                          token=credentials["token"],
                                          url=cls.url,
                                          method="GET",
                                          params=params)
            raw_reports = raw_data.get("reports")
            if not raw_reports:
                break
            reports.extend(raw_reports)
        for report in reports:
            raw_datetime = datetime.datetime.strptime(
                report['generation_date'], "%Y-%m-%dT%H:%M:%S.%f%z")
            raw_datetime = raw_datetime + \
                parse_utc_offset(credentials["timeUTCOffset"])
            report['generation_date'] = datetime.datetime.strftime(raw_datetime, "%Y-%m-%d %H:%M:%S")
        return reports

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
    async def templates(cls, credentials: dict):
        result = await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=f"/api/v1/report_templates",
                                  method="GET")
        return result.get("templates", {})
