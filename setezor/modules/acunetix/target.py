import asyncio
import json
import re
from typing import Union
from .utils import send_request
from .schemes.target import Target as TargetScheme, TargetForm, TargetFormBase


class Target:
    url = "/api/v1/targets"

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
        targets: list[TargetScheme] = raw_data.get("targets")
        if not targets:
            return targets
        while True:
            params["c"] += 100
            raw_data = await send_request(base_url=credentials["url"],
                                          token=credentials["token"],
                                          url=cls.url,
                                          method="GET",
                                          params=params)
            raw_targets = raw_data.get("targets")
            if not raw_targets:
                break
            targets.extend(raw_targets)
        for target in targets:
            config = await send_request(base_url=credentials["url"],
                                        token=credentials["token"],
                                        url=f"{
                                            cls.url}/{target['target_id']}/configuration",
                                        method="GET")
            if config["custom_cookies"]:
                target["cookies"] = "\n".join(
                    [f"{obj["url"]} | {obj["cookie"]}" for obj in config["custom_cookies"]])
            else:
                target["cookies"] = ""
            target["headers"] = "\n".join(config["custom_headers"])
            if config["proxy"]["enabled"]:
                target["proxy"] = f"address: {config["proxy"]["address"]}:{
                    config["proxy"]["port"]}\n"
                if config["proxy"].get("username"):
                    target["proxy"] += f"username: {
                        config["proxy"]["username"]}"
            else:
                target["proxy"] = ""
        return targets

    @classmethod
    async def get_by_id(cls, id: str, credentials: dict):
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=f"{cls.url}/{id}",
                                  method="GET")

    @classmethod
    async def create(cls, payload: dict, credentials: dict) -> Union[int, str]:
        group_id = payload.get("group_id", None)
        target_form = TargetFormBase(**payload)
        if group_id:
            data = TargetForm(groups=[group_id], targets=[target_form])
        else:
            data = TargetForm(groups=[], targets=[target_form])
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=f"{cls.url}/add",
                                  method="POST",
                                  data=data.model_dump_json())

    @classmethod
    async def delete(cls, id: str, credentials: dict) -> None:
        data = json.dumps({
            "target_id_list": [id]
        })
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=f"{cls.url}/delete",
                                  method="POST",
                                  data=data)

    @classmethod
    async def set_scan_speed(cls, targets_ids: list[str], scan_speed: str, credentials: dict):
        scan_speed_json = json.dumps({"scan_speed": scan_speed})
        scan_speed_reqs = []
        for target_id in targets_ids:
            task = asyncio.create_task(send_request(base_url=credentials["url"],
                                                    token=credentials["token"],
                                                    url=f"{
                                                        cls.url}/{target_id}/configuration",
                                                    method="PATCH",
                                                    data=scan_speed_json))
            scan_speed_reqs.append(task)
        await asyncio.gather(*scan_speed_reqs)

    @classmethod
    async def set_proxy(cls, id: str, payload: dict, credentials: dict) -> None:
        if not payload:
            data = json.dumps({"proxy": {"enabled": False}})
        else:
            payload["enabled"] = True
            if not payload.get("username") or not payload.get("password"):
                payload.pop("username",None)
                payload.pop("password",None)
            data = json.dumps({"proxy": payload})
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=f"{cls.url}/{id}/configuration",
                                  method="PATCH",
                                  data=data)

    @classmethod
    async def set_cookies(cls, id: str, payload: dict, credentials: dict) -> None:
        if not payload:
            data = json.dumps({"custom_cookies": []})
        else:
            raw_data = []
            for i in range(len(payload) // 3):
                raw_data.append({
                    "url": payload[f"url{i + 1}"],
                    "cookie": f"{payload[f"key{i + 1}"]}={payload[f"value{i + 1}"]}"
                })
            data = json.dumps({"custom_cookies": raw_data}, indent=4)
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=f"{cls.url}/{id}/configuration",
                                  method="PATCH",
                                  data=data)

    @classmethod
    async def set_headers(cls, id: str, payload: dict, credentials: dict) -> None:
        if not payload:
            data = json.dumps({"custom_headers": []})
        else:
            raw_data = []
            for i in range(len(payload) // 2):
                raw_data.append(
                    f"{payload[f"key{i + 1}"]}: {payload[f"value{i + 1}"]}")
            data = json.dumps({"custom_headers": raw_data}, indent=4)
        return await send_request(base_url=credentials["url"],
                                  token=credentials["token"],
                                  url=f"{cls.url}/{id}/configuration",
                                  method="PATCH",
                                  data=data)

    @classmethod
    async def get_target_scans(cls, id: str, credentials: dict):
        params = {"l": 100, "c": 0, "q": f"target_id:{id};"}
        raw_data = await send_request(base_url=credentials["url"],
                                      token=credentials["token"],
                                      url="/api/v1/scans",
                                      method="GET",
                                      params=params)
        if raw_data.get("code"):
            return {}
        scans: list[TargetScheme] = raw_data.get("scans")
        if not scans:
            return scans
        while True:
            params["c"] += 100
            raw_data = await send_request(base_url=credentials["url"],
                                          token=credentials["token"],
                                          url="/api/v1/scans",
                                          method="GET",
                                          params=params)
            raw_targets = raw_data.get("scans")
            if not raw_targets:
                break
            scans.extend(raw_targets)
        return scans


    @classmethod
    def create_urls(cls, payload):
        new_targets = []
        if payload.get("http_ports"):
            for port in payload["http_ports"].split(","):
                address = f"http://{payload.get("target_ip_address")}:{port}"
                new_targets.append(address)
        if payload.get("https_ports"):
            for port in payload["https_ports"].split(","):
                address = f"https://{payload.get("target_ip_address")}:{port}"
                new_targets.append(address)
        return new_targets


