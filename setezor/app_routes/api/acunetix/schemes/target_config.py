import enum
from typing import Literal
from pydantic import BaseModel, IPvAnyAddress


class CookieTarget(BaseModel):
    url: str = "http://localhost"
    cookie: str


class Authentication(BaseModel):
    enabled: bool = False


class Login(BaseModel):
    kind: str = "none"


class ProxyEnable(BaseModel):
    protocol: Literal["http"] = "http"
    address: IPvAnyAddress
    port: int
    username: str | None = None
    password: str | None = None

    class Config:
        json_schema_extra = {
            'examples': [
                {
                    'protocol': 'http',
                    'address': "127.0.0.1",
                    'port': 80,
                    'username': "",
                    'password': ""
                },
            ]
        }


class Proxy(ProxyEnable):
    enabled: bool = False


class SshCredentials(BaseModel):
    kind: str = "none"
    port: int | None = None


class ScanSpeedValues(str,enum.Enum):
    sequential = "sequential"
    slow = "slow"
    moderate = "moderate"
    fast = "fast"


class ScanSpeed(BaseModel):
    scan_speed: ScanSpeedValues


class TargetConfiguration(BaseModel):
    ad_blocker: bool
    authentication: Authentication
    case_sensitive: str
    client_certificate_password: str = ""
    custom_headers: list[str] | None = None
    custom_cookies: list[CookieTarget] | None = None
    debug: bool
    default_scanning_profile_id: str | None = None
    excluded_paths: list[str]
    limit_crawler_scope: bool
    login: Login
    preseed_mode: str | None = None
    proxy: Proxy
    restrict_scans_to_import_files: bool | None = None
    scan_speed: ScanSpeedValues
    sensor: bool | None = None
    sensor_secret: str | None = None
    skip_login_form: bool
    ssh_credentials: SshCredentials
    technologies: list[str]
    user_agent: str


class Header(BaseModel):
    key: str
    value: str


class Cookie(BaseModel):
    url: str
    key: str
    value: str
    class Config:
        json_schema_extra = {
            'examples': [
                {
                    'url': 'https://ya.ru',
                    'key': "TOKEN",
                    'value': "abcdef1234fbca",
                },
            ]
        }
