from typing import Annotated, List, Literal
from fastapi import APIRouter, Depends

from setezor.dependencies.project import get_current_project, get_current_scan_id, role_required
from setezor.models import Task
from setezor.schemas.task import DNSTaskPayload, \
    MasscanScanTaskPayload, \
    NmapParseTaskPayload, \
    ScapySniffTaskPayload, \
    WHOISTaskPayload, \
    DomainTaskPayload, \
    NmapScanTaskPayload, \
    WappalyzerParseTaskPayload, \
    CertInfoTaskPayload, \
    ScapyParseTaskPayload, \
    MasscanLogTaskPayload, \
    SnmpBruteCommunityStringPayload, \
    SpeedTestTaskPayload
from setezor.services import TasksService
from setezor.managers import TaskManager
from setezor.services.project_service import ProjectService
from setezor.services.software import SoftwareService
from setezor.tasks import DNSTask, WhoisTask, SdFindTask, NmapParseTask
from setezor.tasks.masscan_scan_task import MasscanScanTask
from setezor.tasks.masscan_parse_task import MasscanLogTask
from setezor.tasks.nmap_scan_task import NmapScanTask
from setezor.tasks.cert_task import CertTask
from setezor.tasks.scapy_scan_task import ScapySniffTask
from setezor.tasks.scapy_logs_task import ScapyLogsTask
from setezor.tasks.wappalyzer_logs_task import WappalyzerLogsTask
from setezor.tasks.cve_refresh_task import CVERefresher
from setezor.tasks.snmp_brute_community_string_task import SnmpBruteCommunityStringTask
from setezor.tasks.speed_test_task import SpeedTestClientTask, SpeedTestServerTask
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/task",
    tags=["Tasks"],
)


@router.get("")
async def list_tasks(
    tasks_service: Annotated[TasksService, Depends(TasksService.new_instance)],
    status: Literal["STARTED", "IN QUEUE", "FINISHED", "FAILED", "CREATED"],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> List[Task]:
    tasks = await tasks_service.list(project_id=project_id, status=status)
    return tasks


@router.post("/{id}/soft_stop")
async def soft_stop_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> bool:
    return await task_manager.soft_stop_task(id=id, project_id=project_id)


@router.post("/{id}/deleteTask")
async def delete_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    id : str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> bool:
    return await task_manager.delete_task(id=id, project_id=project_id)


@router.post("/dns_task", status_code=201)
async def create_dns_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    dns_task_payload: DNSTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    await task_manager.create_job(
        job=DNSTask,
        project_id=project_id,
        scan_id=scan_id,
        **dns_task_payload.model_dump()
    )


@router.post('/sd_find', status_code=201)
async def create_sd_find(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    domain_task_payload: DomainTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    await task_manager.create_job(
        job=SdFindTask,
        project_id=project_id,
        scan_id=scan_id,
        **domain_task_payload.model_dump()
    )


@router.post("/whois_task", status_code=201)
async def create_whois_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    whois_task_payload: WHOISTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    await task_manager.create_job(
        job=WhoisTask,
        project_id=project_id,
        scan_id=scan_id,
        **whois_task_payload.model_dump()
    )


@router.post("/masscan_scan_task", status_code=201)
async def create_masscan_scan_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    masscan_scan_task_payload: MasscanScanTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    await task_manager.create_job(
        job=MasscanScanTask,
        project_id=project_id,
        scan_id=scan_id,
        **masscan_scan_task_payload.model_dump()
    )


@router.post("/masscan_log_task", status_code=201)
async def create_masscan_log_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    masscan_log_task_payload: MasscanLogTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    await task_manager.create_local_job(
        job=MasscanLogTask,
        project_id=project_id,
        scan_id=scan_id,
        **masscan_log_task_payload.model_dump()
    )


@router.post("/nmap_scan_task", status_code=201)
async def create_nmap_scan_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    nmap_scan_task_payload: NmapScanTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    task: Task = await task_manager.create_job(
        job=NmapScanTask,
        project_id=project_id,
        scan_id=scan_id,
        **nmap_scan_task_payload.model_dump()
    )


@router.post("/nmap_parse_task", status_code=201)
async def create_nmap_parse_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    nmap_parse_task_payload: NmapParseTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    task: Task = await task_manager.create_local_job(
        job=NmapParseTask,
        project_id=project_id,
        scan_id=scan_id,
        **nmap_parse_task_payload.model_dump()
    )


@router.post("/cert_info_task", status_code=201)
async def create_cert_info_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    cert_info_task_payload: CertInfoTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    await task_manager.create_job(
        job=CertTask,
        project_id=project_id,
        scan_id=scan_id,
        **cert_info_task_payload.model_dump()
    )


@router.post("/scapy_sniff_task", status_code=201)
async def create_scapy_sniff_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    scapy_sniff_task_payload: ScapySniffTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    await task_manager.create_job(
        job=ScapySniffTask,
        project_id=project_id,
        scan_id=scan_id,
        **scapy_sniff_task_payload.model_dump()
    )


@router.post("/scapy_parse_task", status_code=201)
async def create_scapy_parse_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    scapy_parse_task_payload: ScapyParseTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    await task_manager.create_local_job(
        job=ScapyLogsTask,
        scan_id=scan_id,
        project_id=project_id,
        **scapy_parse_task_payload.model_dump()
    )


@router.post("/wappalyzer_log_parse", status_code=201)
async def create_wappalyzer_parse_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    wappalyzer_parse_task_payload: WappalyzerParseTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    await task_manager.create_local_job(
        job=WappalyzerLogsTask,
        scan_id=scan_id,
        project_id=project_id,
        **wappalyzer_parse_task_payload.model_dump()
    )


@router.post("/refresh_cve", status_code=201)
async def cve_refresh_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    project_service: Annotated[ProjectService, Depends(ProjectService.new_instance)],
    software_service: Annotated[SoftwareService, Depends(SoftwareService.new_instance)],
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> None:
    await task_manager.create_local_job(
        job=CVERefresher,
        scan_id=scan_id,
        project_id=project_id,
        project_service=project_service,
        software_service=software_service,
    )


@router.post("/snmp_brute_communitystring_task", status_code=201)
async def create_snmp_brute_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    payload: SnmpBruteCommunityStringPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
) -> None:
    await task_manager.create_job(
        job=SnmpBruteCommunityStringTask,
        scan_id=scan_id,
        project_id=project_id,
        **payload.model_dump()
    )



@router.post("/speed_test_task", status_code=201)
async def create_speed_test_task(
    task_manager: Annotated[TaskManager, Depends(TaskManager.new_instance)],
    payload: SpeedTestTaskPayload,
    scan_id: str = Depends(get_current_scan_id),
    project_id: str = Depends(get_current_project),
) -> None:
    await task_manager.create_job(
        job=SpeedTestServerTask,
        scan_id=scan_id,
        project_id=project_id,
        **payload.model_dump()
    )