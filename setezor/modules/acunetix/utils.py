import datetime
from typing import Any, Literal
import aiohttp
from .schemes.scan import ScanWithInterval
from .schemes.target import TargetForm, TargetFormBase


async def send_request(base_url: str,
                       token: str,
                       url: str, method: Literal["GET", "POST", "PATCH", "DELETE"],
                       params: dict[str, Any] = None,
                       data: dict[str, Any] = None) -> dict | list | None:
    headers = {'content-type': 'application/json',
               'x-auth': token}
    cookies = {
        "ui_session": token
    }
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
        match method:
            case "GET":
                async with session.get(base_url + url,
                                       params=params,
                                       ssl=False,
                                       headers=headers) as resp:
                    if resp.content_type == "application/json":
                        return await resp.json()
                    else:
                        filename = resp.content_disposition.parameters.get("filename", "") if resp.content_disposition else ""
                        data = await resp.read()
                        return filename, data, resp.status
            case "POST":
                async with session.post(base_url + url,
                                        params=params,
                                        data=data,
                                        ssl=False,
                                        headers=headers) as resp:
                    if not resp.status in (200, 201, 204):
                        message = (await resp.json())["message"]
                        return resp.status, message
                    try:
                        return resp.status, await resp.json()
                    except:
                        return resp.status, await resp.text()
            case "PATCH":
                async with session.patch(base_url + url,
                                         params=params,
                                         data=data,
                                         ssl=False,
                                         headers=headers) as resp:
                    return resp.status
            case _:
                return {}


def parse_utc_offset(offset_str):
    hours, minutes = map(int, offset_str.split(':'))
    return datetime.timedelta(hours=hours, minutes=minutes)


def convert_to_datetime_for_scan(date: datetime.date, 
                                 time: datetime.time, 
                                 offset: str,
                                 interval: datetime.timedelta | None = None):
    if not interval:
        interval = datetime.timedelta()
    raw_datetime = datetime.datetime.combine(date, time) - parse_utc_offset(offset) + interval

    date = raw_datetime.date()
    time = raw_datetime.time()

    month = f"{date.month:02}"
    day = f"{date.day:02}"

    hour = f"{time.hour:02}"
    minute = f"{time.minute:02}"

    datetime_date = f"{date.year}{month}{day}"
    datetime_time = f"{hour}{minute}00"
    return f"{datetime_date}T{datetime_time}"


def get_new_interval(interval: datetime.timedelta, to_add: datetime.time):
    td_to_add = datetime.timedelta(hours=to_add.hour, minutes=to_add.minute)
    return interval + td_to_add


async def create_scan_for_db_obj(credentials: dict, payload: dict) -> bool:
    new_targets = []
    if payload.get("http_ports"):
        for port in payload["http_ports"].split(","):
            address = f"http://{payload.get("target_ip_address")}:{port}"
            target_form = TargetFormBase(address=address, description="")
            new_targets.append(target_form)
    if payload.get("https_ports"):
        for port in payload["https_ports"].split(","):
            address = f"https://{payload.get("target_ip_address")}:{port}"
            target_form = TargetFormBase(address=address, description="")
            new_targets.append(target_form)

    data = TargetForm(groups=[], targets=[*new_targets])
    raw_data = await send_request(base_url=credentials["url"],
                                  # создание множества таргетов
                                  token=credentials["token"],
                                  url="/api/v1/targets/add",
                                  method="POST",
                                  data=data.model_dump_json())

    new_targets = [target["target_id"] for target in raw_data.get("targets")]
    base = ScanWithInterval(**payload)

    await set_scan_speed_for_targets(credentials=credentials,
                                     scan_speed=base.scan_speed,
                                     targets_ids=new_targets)
    await create_scan_for_targets(credentials=credentials,
                                  profile_id=base.profile_id,
                                  targets_ids=new_targets,
                                  start_date=base.date,
                                  start_time=base.start_time,
                                  interval=base.interval)
    return True
