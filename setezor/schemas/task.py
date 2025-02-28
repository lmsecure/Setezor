
from typing import Optional
from pydantic import BaseModel
from pydantic.networks import IPv4Address

class TaskStatus:
    pending = "PENDING"
    started = "STARTED"
    in_queue = "IN QUEUE"
    finished = "FINISHED"
    failed = "FAILED"
    created = "CREATED"


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
    project_id: str
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

class WebSocketMessageForProject(WebSocketMessage):
    project_id: str


class DNSTaskPayload(BaseModel):
    domain: str
    agent_id: str

class DomainTaskPayload(BaseModel):
    domain: str
    crt_sh: bool
    agent_id: str

class WHOISTaskPayload(BaseModel):
    target: str
    agent_id: str

class MasscanScanTaskPayload(BaseModel):
    interface_ip_id: str
    interface: str
    agent_id: str
    target: IPv4Address
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
    mac: str

class NmapScanTaskPayload(BaseModel):
    targetIP: str #IPv4Address
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

class NmapParseTaskPayload(BaseModel):
    agent_id: str
    file: str
    filename: str
    interface_ip_id: str
    ip: IPv4Address
    mac: str

class CertInfoTaskPayload(BaseModel):
    agent_id: str
    port: int
    target: str

class ScapySniffTaskPayload(BaseModel):
    agent_id: str
    iface: str

class ScapyParseTaskPayload(BaseModel):
    agent_id: str
    file: str

class WappalyzerParseTaskPayload(BaseModel):
    log_file: str
    groups: list[str]
    agent_id: str

class SnmpBruteCommunityStringPayload(BaseModel):
    agent_id: str
    target_ip: str
    target_port: int
    community_strings_file: str