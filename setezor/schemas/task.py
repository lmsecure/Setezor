from typing import Any, Optional
from enum import Enum, StrEnum
from pydantic import BaseModel, field_validator, conint
from urllib.parse import urlparse
from pydantic.networks import IPv4Address, IPv4Network
from setezor.schemas.domain import DomainStr
import json

PortNumber = conint(ge=1, le=65535)

class TaskStatus(StrEnum):
    created = "CREATED"
    registered = "REGISTERED"
    processing_on_agent = "PROCESSING_ON_AGENT"
    finished_on_agent = "FINISHED_ON_AGENT"
    processing_on_server = "PROCESSING_ON_SERVER"
    pre_canceled = "PRE_CANCELED"
    canceled = "CANCELED"
    soft_stopped = "SOFTSTOPPED"
    finished = "FINISHED"
    failed = "FAILED"


class TaskNotify(BaseModel):
    id: str
    name: str
    status: str
    traceback: str | None

    def to_str(self):
        return json.dumps(self.model_dump())

class TaskSchema(BaseModel):
    id: str
    status: str

    class Config:
        from_orm = True


class TaskSchemaAdd(BaseModel):
    status: str


class TaskSchemaEditStatus(BaseModel):
    status: str



class TaskPayload(BaseModel):
    task_id: str
    project_id: Optional[str]
    agent_id: str
    job_params: dict
    job_name: str


class TaskStartForm(BaseModel):
    id: str
    project_id: str
    agents_chain: list[str]

class TaskSoftStopForm(BaseModel):
    id: str
    agents_chain: list[str]

class WebSocketMessage(BaseModel):
    title: str
    text: str
    type: str
    command: str = "notify"
    user_id: str | None = None

class WebSocketMessageForProject(WebSocketMessage):
    project_id: str


class TaskPayloadWithScopeID(BaseModel):
    scope_id: str | None = None

class DnsRecords(str, Enum):
    A = "A"
    NS = "NS"
    MX = "MX"
    CNAME = "CNAME"
    SOA = "SOA"
    TXT = "TXT"
    AAAA = "AAAA"
    SRV = "SRV"
    PTR = "PTR"

class DNSTaskPayload(TaskPayloadWithScopeID):
    agent_id: str
    domain: DomainStr | None = None
    records: list[DnsRecords] | None = list(DnsRecords)
    ns_servers: list[IPv4Address] | None = None

class DomainTaskPayload(TaskPayloadWithScopeID):
    agent_id: str
    domain: DomainStr | None = None
    dict_file: str | None = None
    crt_sh: Optional[bool] = False

class WHOISShdwsTaskPayload(TaskPayloadWithScopeID):
    target: IPv4Address | None = None
    agent_id: str

class RDAPTaskPayload(TaskPayloadWithScopeID):
    target: DomainStr | None = None
    agent_id: str

class MasscanScanTaskPayload(TaskPayloadWithScopeID):
    interface_ip_id: str
    interface: str
    agent_id: str
    target: IPv4Network | None = None
    ping: bool
    ports: str | None = None
    format: str
    wait: int
    search_udp_port: bool
    source_port: Optional[int]
    max_rate: Optional[int]

class MasscanLogTaskPayload(BaseModel):
    agent_id: str
    filename: str
    file: str
    interface_ip_id: str
    ip: IPv4Address

class NmapScanTaskPayload(TaskPayloadWithScopeID):
    targetIP: IPv4Network  | None = None #IPv4Address
    agent_id: str
    interface_ip_id: str
    interface: str
    targetPorts: str
    traceroute: bool                    # "--traceroute"
    serviceVersion: bool                # "-sV"
    stealthScan: bool                   # "-O"
    skipDiscovery: bool                 # "-Pn"
    scanTechniques: Optional[str]       # ["-sS", "-sT", "-sA", "-sW" "-sM" "-sU"]
    portsDiscovery: Optional[str]       # ["-PA", "-PS", "-PU", "-PY"]
    requestDiscovery: Optional[str]     # ["-PE", "-PP", "-PM"]
    timingTemplate: str | None = None
    minRtt: str | None = None
    maxRtt: str | None = None
    initialRtt: str | None = None
    maxRetries: str | None = None
    scanDelay: str | None = None
    maxTcpDelay: str | None = None
    maxUdpDelay: str | None = None
    hostTimeout: str | None = None
    minRate: str | None = None
    maxRate: str | None = None
    maxParallelism: str | None = None

class NmapParseTaskPayload(BaseModel):
    agent_id: str
    file: str
    filename: str
    interface_ip_id: str
    ip: IPv4Address | None = None
    mac: str | None = None

class CertInfoTaskPayload(TaskPayloadWithScopeID):
    agent_id: str
    port: PortNumber | None = None
    target: DomainStr | IPv4Address | None = None

class ScapySniffTaskPayload(BaseModel):
    agent_id: str
    iface: str

class ScapyParseTaskPayload(BaseModel):
    agent_id: str
    file: str
    filename: str

class WappalyzerParseTaskPayload(BaseModel):
    file: str
    filename: str
    groups: list[str]
    agent_id: str

class SnmpBruteCommunityStringPayload(BaseModel):
    agent_id: str
    target_ip: IPv4Address | None = None
    target_port: PortNumber | None = None
    community_strings_file: str

class SpeedTestTaskPayload(BaseModel):
    agent_id: str
    agent_id_from: str
    ip_id_from: str
    ip_id_to: str
    target_ip: IPv4Address
    target_port: PortNumber
    duration: Optional[int] = 5
    packet_size: Optional[int] = 1400
    protocol: Optional[int] = 0

class DNSAScreenshotTaskPayload(BaseModel):
    agent_id: str
    url: str
    timeout: Optional[float] = 20.0

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Валидация URL"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain")
        return v


class IPInfoTaskPayload(TaskPayloadWithScopeID):
    agent_id: str
    target: IPv4Address | None = None
    fields: Optional[list] = [
        'as', 'isp', 'lat', 'lon', 'org', 'zip', 'city',
        'proxy', 'query', 'asname', 'mobile', 'offset',
        'region', 'status', 'country', 'hosting', 'message',
        'reverse', 'currency', 'district', 'timezone',
        'continent', 'regionName', 'countryCode', 'continentCode'
    ]


class ParseSiteTaskPayload(TaskPayloadWithScopeID):
    agent_id: str
    url: str | None = None
    with_screenshot: bool
    with_wappalyzer: bool
    timeout: float

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Валидация URL"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain")
        return v

class PushModuleTaskPayload(BaseModel):
    agent_id: str
    module_names: list[str]


class TaskLog(BaseModel):
    type: str
    file_name: str
    file_data: Any
