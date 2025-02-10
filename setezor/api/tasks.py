from typing import List, Literal
from fastapi import APIRouter, BackgroundTasks, Depends, Body
from setezor.dependencies.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, get_current_scan_id, role_required
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.models import Task
from setezor.schemas.task import DNSTaskPayload, MasscanScanTaskPayload, NmapParseTaskPayload, ScapySniffTaskPayload, WHOISTaskPayload, DomainTaskPayload, NmapScanTaskPayload, WappalyzerParseTaskPayload, WebSocketMessage, WebSocketMessageForProject, CertInfoTaskPayload, ScapyParseTaskPayload, MasscanLogTaskPayload
from setezor.services import TasksService
from setezor.managers import TaskManager
from setezor.tasks import DNSTask, WhoisTask, SdFindTask, NmapParseTask
from setezor.tasks.masscan_scan_task import MasscanScanTask
from setezor.tasks.masscan_parse_task import MasscanLogTask
from setezor.tasks.nmap_scan_task import NmapScanTask
from setezor.tasks.cert_task import CertTask
from setezor.tasks.scapy_scan_task import ScapySniffTask
from setezor.tasks.scapy_logs_task import ScapyLogsTask
from setezor.tasks.wappalyzer_logs_task import WappalyzerLogsTask
from setezor.tasks.cve_refresh_task import CVERefresher


router = APIRouter(
    prefix="/task",
    tags=["Tasks"],
)


@router.get("")
async def list_tasks(
    uow: UOWDep,
    status: Literal["STARTED", "IN QUEUE", "FINISHED", "FAILED","CREATED"],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner", "viewer"]))
) -> List[Task]:
    tasks = await TasksService.list(uow=uow, project_id=project_id, status=status)
    return tasks

@router.post("/{id}/soft_stop")
async def soft_stop_task(
    uow: UOWDep,
    id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> bool:
    return await TaskManager.soft_stop_task(uow=uow, id=id, project_id=project_id)

@router.post("/dns_task", status_code=201)
async def create_dns_task(
    uow: UOWDep,
    dns_task_payload: DNSTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> Task:
    task: Task = await TaskManager.create_job(
        job=DNSTask,
        uow=uow,
        project_id=project_id,
        scan_id=scan_id,
        **dns_task_payload.model_dump()
    )
    return task


@router.post('/sd_find', status_code=201)
async def create_sd_find(
    uow: UOWDep,
    domain_task_payload: DomainTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> Task:
    task: Task = await TaskManager.create_job(
        job=SdFindTask,
        uow=uow,
        project_id=project_id,
        scan_id=scan_id,
        **domain_task_payload.model_dump()
    )
    return task


@router.post("/whois_task", status_code=201)
async def create_whois_task(
    uow: UOWDep,
    whois_task_payload: WHOISTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> Task:
    task: Task = await TaskManager.create_job(
        job=WhoisTask,
        uow=uow,
        project_id=project_id,
        scan_id=scan_id,
        **whois_task_payload.model_dump()
    )
    return task


@router.post("/masscan_scan_task", status_code=201)
async def create_masscan_scan_task(
    uow: UOWDep,
    masscan_scan_task_payload: MasscanScanTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> Task:
    task: Task = await TaskManager.create_job(
        job=MasscanScanTask,
        uow=uow,
        project_id=project_id,
        scan_id=scan_id,
        **masscan_scan_task_payload.model_dump()
    )
    return task


@router.post("/masscan_log_task", status_code=201)
async def create_masscan_log_task(
    uow: UOWDep,
    masscan_log_task_payload: MasscanLogTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> int:
    task: Task = await TaskManager.create_local_job(
        job=MasscanLogTask,
        uow=uow,
        project_id=project_id,
        scan_id=scan_id,
        **masscan_log_task_payload.model_dump()
    )
    return 1
    

@router.post("/nmap_scan_task", status_code=201)
async def create_nmap_scan_task(
    uow: UOWDep,
    nmap_scan_task_payload: NmapScanTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> Task:
    task: Task = await TaskManager.create_job(
        job=NmapScanTask,
        uow=uow,
        project_id=project_id,
        scan_id=scan_id,
        **nmap_scan_task_payload.model_dump()
    )
    return task

@router.post("/nmap_parse_task", status_code=201)
async def create_nmap_parse_task(
    uow: UOWDep,
    nmap_parse_task_payload: NmapParseTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> int:
    task: Task = await TaskManager.create_local_job(
        job=NmapParseTask,
        uow=uow,
        project_id=project_id,
        scan_id=scan_id,
        **nmap_parse_task_payload.model_dump()
    )
    return 1

@router.post("/cert_info_task", status_code=201)
async def create_cert_info_task(
    uow: UOWDep,
    cert_info_task_payload: CertInfoTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> int:
    task: Task = await TaskManager.create_job(
        job=CertTask,
        uow=uow,
        project_id=project_id,
        scan_id=scan_id,
        **cert_info_task_payload.model_dump()
    )
    return 1

@router.post("/scapy_sniff_task", status_code=201)
async def create_scapy_sniff_task(
    uow: UOWDep,
    scapy_sniff_task_payload: ScapySniffTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> int:
    task: Task = await TaskManager.create_job(
        job=ScapySniffTask,
        uow=uow,
        project_id=project_id,
        scan_id=scan_id,
        **scapy_sniff_task_payload.model_dump()
    )
    return 1

@router.post("/scapy_parse_task", status_code=201)
async def create_scapy_parse_task(
    uow: UOWDep,
    scapy_parse_task_payload: ScapyParseTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> int:
    task: Task = await TaskManager.create_local_job(
        job=ScapyLogsTask,
        uow=uow,
        scan_id=scan_id,
        project_id=project_id,
        **scapy_parse_task_payload.model_dump()
    )
    return 1


@router.post("/wappalyzer_log_parse", status_code=201)
async def create_wappalyzer_parse_task(
    uow: UOWDep,
    wappalyzer_parse_task_payload: WappalyzerParseTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> int:
    task: Task = await TaskManager.create_local_job(
        job=WappalyzerLogsTask,
        uow=uow,
        scan_id=scan_id,
        project_id=project_id,
        **wappalyzer_parse_task_payload.model_dump()
    )
    return 1

@router.post("/refresh_cve", status_code=201)
async def cve_refresh_task(
    uow: UOWDep,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required(["owner"]))
) -> int:
    task: Task = await TaskManager.create_local_job(
        job=CVERefresher,
        uow=uow,
        scan_id=scan_id,
        project_id=project_id,
    )
    return 1