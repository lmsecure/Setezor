import asyncio
import json
from .utils import convert_to_datetime_for_scan, get_new_interval, send_request, parse_utc_offset
import datetime
from .schemes.scan import TargetScanStart, GroupScanStart
from .target import Target
from .schemes.group import GroupTargets
from .group import Group
from .schemes.scan import ScanWithInterval
from .schemes.target import TargetForm, TargetFormBase


class Scan:

    url = "/api/v1/scans"

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
        scans = raw_data.get("scans")
        while True:
            params["c"] += 100
            raw_data = await send_request(base_url=credentials["url"],
                                          token=credentials["token"],
                                          url=cls.url,
                                          method="GET",
                                          params=params)
            raw_scans = raw_data.get("scans")
            if not raw_scans:
                break
            scans.extend(raw_data.get("scans"))

        for scan in scans:
            scan['target'] = scan['target']['address']
            scan['last_scan_session_status'] = scan["current_session"]["status"]
            if scan["current_session"]["start_date"]:
                raw_datetime = datetime.datetime.strptime(
                    scan["current_session"]["start_date"], "%Y-%m-%dT%H:%M:%S.%f%z")
            else:
                raw_datetime = datetime.datetime.strptime(
                    scan["schedule"]["start_date"], "%Y-%m-%dT%H:%M:%S%z")
            raw_datetime = raw_datetime + \
                parse_utc_offset(credentials["timeUTCOffset"])
            scan["start_date"] = datetime.datetime.strftime(raw_datetime, "%Y-%m-%d %H:%M:%S")
        return scans

    @classmethod
    async def get_by_id(cls, id: str, credentials: dict):
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  method="GET",
                                  url=f"{cls.url}/{id}")

    @classmethod
    async def get_vulnerabilities(cls, id: str, result_id: str, credentials: dict):
        params = {
            "l": 100,
            "q": "status:!ignored;status:!fixed;",
        }
        vulnerabilities = []
        while True:
            raw_data = await send_request(base_url=credentials["url"],
                                          token=credentials["token"],
                                          url=f"/api/v1/scans/{id}/results/{
                                              result_id}/vulnerabilities",
                                          method="GET",
                                          params=params)
            for vuln in raw_data.get("vulnerabilities", []):
                vulnerabilities.append(vuln)
            pagination = raw_data.get("pagination")
            if not pagination: break
            cursors = pagination.get("cursors")
            if len(cursors) == 1:
                break
            params.update({"c": cursors[1]})
        return vulnerabilities

    @classmethod
    async def get_statistics(cls, credentials: dict, scan_id: str, result_id: str):
        return await send_request(base_url=credentials["url"],
                                          token=credentials["token"],
                                          url=f"/api/v1/scans/{scan_id}/results/{result_id}/statistics",
                                          method="GET")

    @classmethod
    async def create_for_targets(cls, credentials: dict, profile_id: str, targets_ids: list[str], start_date: datetime.date,
                                 start_time: datetime.time, interval: datetime.time | None = None):
        raw_data = {
            "profile_id": profile_id,
            "incremental": False,
            "schedule": {
                "disable": False,
                "start_date": "",
                "time_sensitive": True
            },
            "target_id": ""
        }
        scans = []
        if interval:
            interval_delta = datetime.timedelta(
                hours=interval.hour, minutes=interval.minute)
        for index, target_id in enumerate(targets_ids):
            if index == 0:
                raw_data["schedule"]["start_date"] = convert_to_datetime_for_scan(date=start_date,
                                                                                  time=start_time,
                                                                                  offset=credentials["timeUTCOffset"])
            else:
                raw_data["schedule"]["start_date"] = convert_to_datetime_for_scan(date=start_date,
                                                                                  time=start_time,
                                                                                  interval=interval_delta,
                                                                                  offset=credentials["timeUTCOffset"])
                interval_delta = get_new_interval(interval_delta, interval)
            raw_data["target_id"] = target_id

            data = json.dumps(raw_data)
            task = asyncio.create_task(send_request(base_url=credentials["url"],
                                                    token=credentials["token"],
                                                    url=f"{cls.url}", method="POST", data=data))
            scans.append(task)
        return await asyncio.gather(*scans)

    @classmethod
    async def create_for_target(cls, payload: dict, credentials: dict):
        target_scan = TargetScanStart(**payload)
        await Target.set_scan_speed(credentials=credentials,
                                    scan_speed=target_scan.scan_speed,
                                    targets_ids=[target_scan.target_id])
        return await cls.create_for_targets(credentials=credentials,
                                            profile_id=target_scan.profile_id,
                                            targets_ids=[
                                                target_scan.target_id],
                                            start_date=target_scan.date,
                                            start_time=target_scan.start_time)

    @classmethod
    async def create_for_group(cls, payload: dict, credentials: dict):
        group_scan = GroupScanStart(**payload)
        raw_targets = await Group.get_targets(id=group_scan.group_id, credentials=credentials)
        targets = GroupTargets(**raw_targets)

        await Target.set_scan_speed(credentials=credentials,
                                    scan_speed=group_scan.scan_speed,
                                    targets_ids=targets.target_id_list)

        return await cls.create_for_targets(credentials=credentials,
                                            profile_id=group_scan.profile_id,
                                            targets_ids=targets.target_id_list,
                                            start_date=group_scan.date,
                                            start_time=group_scan.start_time,
                                            interval=group_scan.interval)

    @classmethod
    async def create_for_db_obj(cls, payload: dict, credentials: dict):
        new_targets = payload.get("target_ids")
        base = ScanWithInterval(**payload)
        await Target.set_scan_speed(credentials=credentials,
                                    scan_speed=base.scan_speed,
                                    targets_ids=new_targets)
        return await cls.create_for_targets(credentials=credentials,
                                            profile_id=base.profile_id,
                                            targets_ids=new_targets,
                                            start_date=base.date,
                                            start_time=base.start_time,
                                            interval=base.interval)

    @classmethod
    async def get_profiles(cls, credentials: dict):
        result = await send_request(base_url=credentials["url"],
                                    token=credentials["token"],
                                    url="/api/v1/scanning_profiles",
                                    method="GET")
        return result.get("scanning_profiles", {})
