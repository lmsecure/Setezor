from typing import Optional
from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse, JSONResponse
from setezor.schemas.acunetix.schemes.report import ReportAddForm
from setezor.db.uow_dependency import UOWDep
from setezor.dependencies.project import get_current_project, role_required
from setezor.services import AcunetixService
from setezor.schemas.acunetix.schemes.group import GroupForm
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/reports"
)

@router.get("")
async def get_acunetix_reports(
    uow: UOWDep,
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await AcunetixService.get_reports(uow=uow, project_id=project_id, acunetix_id=acunetix_id)

@router.post("")
async def create_acunetix_report(
    uow: UOWDep,
    create_report_form: ReportAddForm, 
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status, msg = await AcunetixService.create_report(uow=uow, project_id=project_id, acunetix_id=acunetix_id, create_report_form=create_report_form)
    return JSONResponse(status_code=status, content=msg)


@router.get("/{report_id}/download")
async def download_report(
    uow: UOWDep,
    report_id: str,
    format: str,
    acunetix_id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    filename, data = await AcunetixService.get_report_file(uow=uow, project_id=project_id, acunetix_id=acunetix_id, report_id=report_id, format=format)
    if format == "pdf":
        content_type = "application/pdf"
    else:
        content_type = "text/html"
    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return Response(content=data, headers=headers, media_type=content_type)


@router.get("/templates")
async def get_reports_templates(
    uow: UOWDep,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await AcunetixService.get_report_templates(uow=uow, project_id=project_id)