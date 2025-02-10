import datetime
from typing import Optional
from pydantic import BaseModel


class SeverityCounts(BaseModel):
    critical: int = 0
    high: int = 0
    info: int = 0
    low: int = 0
    medium: int = 0


class TargetFormBase(BaseModel):
    address: str
    description: str = ""
    type: str | None = "default"
    criticality: int = 10


class TargetForm(BaseModel):
    groups: list[str] | None = []
    targets: list[TargetFormBase]



class TargetToSync(BaseModel):
    acunetix_id: str
    in_acunetix_id: str
    in_setezor_id: Optional[str]
    scope_id: str
    address: str

class SyncPayload(BaseModel):
    dt_from: datetime.date
    dt_to: datetime.date
    targets: list[TargetToSync]


class TargetBase(BaseModel):
    address: str
    criticality: int
    description: str
    fqdn: str
    type: str | None = None
    domain: str | None = None
    target_id: str
    target_type: None = None


class Target(TargetBase):
    agents: list[str] | None = None
    continuous_mode: bool | None = None
    default_overrides: None = None
    default_scanning_profile_id: str | None = None
    deleted_at: str | None = None
    fqdn_hash: str | None = None
    fqdn_status: str | None = None
    fqdn_tm_hash: str | None = None
    issue_tracker_id: str | None = None
    last_scan_date: str | None = None
    last_scan_id: str | None = None
    last_scan_session_id: str | None = None
    last_scan_session_status: str | None = None
    manual_intervention: bool | None = None
    severity_counts: SeverityCounts | None = None
    threat: int | None = None
    verification: str | None = None