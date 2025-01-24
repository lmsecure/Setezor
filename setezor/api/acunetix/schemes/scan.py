from pydantic import BaseModel
import datetime

from ..schemes.target_config import ScanSpeedValues


class SeverityCounts(BaseModel):
    critical: int
    high: int
    info: int
    low: int
    medium: int


class CurrentSession(BaseModel):
    event_level: int
    progress: int | None = None
    scan_session_id: str | None = None
    severity_counts: SeverityCounts | None = None
    start_date: str | None = None
    status: str
    threat: int


class Schedule(BaseModel):
    disable: bool
    history_limit: int | None = None
    recurrence: str | None = None
    start_date: str | None = None
    time_sensitive: bool
    triggerable: bool


class Target(BaseModel):
    address: str
    criticality: int
    description: str
    type: str


class Scan(BaseModel):
    criticality: int
    current_session: CurrentSession
    incremental: bool
    max_scan_time: int
    next_run: str | None = None
    profile_id: str
    profile_name: str
    report_template_id: str | None = None
    scan_id: str
    schedule: Schedule
    target: Target
    target_id: str


class ScanBase(BaseModel):
    scan_speed: ScanSpeedValues
    date: datetime.date
    start_time: datetime.time
    profile_id: str


class TargetScanStart(ScanBase):
    target_id: str


class ScanWithInterval(ScanBase):
    interval: datetime.time

class GroupScanStart(ScanWithInterval):
    group_id: str

    class Config:
        json_schema_extra = {
            'examples': [
                {
                    "group_id": "2004b52c-6178-4534-b2f7-49028db4a05b",
                    "scan_speed": "fast",
                    "date": "2024-08-01",
                    "start_time": "10:30",
                    "profile_id": "11111111-1111-1111-1111-111111111111",
                    "interval": "01:30"
                },
            ]
        }


class ScanningProfile(BaseModel):
    checks: list[str]
    custom: bool
    name: str
    profile_id: str
    sort_order: int


class ScanResult(BaseModel):
    end_date: str
    result_id: str
    scan_id: str
    start_date: str
    status: str
