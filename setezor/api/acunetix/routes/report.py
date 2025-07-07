from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse, JSONResponse
from setezor.schemas.acunetix.schemes.report import ReportAddForm
from setezor.dependencies.project import get_current_project, role_required
from setezor.services import AcunetixService
from setezor.schemas.acunetix.schemes.group import GroupForm
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/reports"
)

@router.get("")
async def get_acunetix_reports(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await acunetix_service.get_reports(project_id=project_id, acunetix_id=acunetix_id)

@router.post("")
async def create_acunetix_report(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    create_report_form: ReportAddForm, 
    acunetix_id: Optional[str] = None,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
):
    status, msg = await acunetix_service.create_report(project_id=project_id, acunetix_id=acunetix_id, create_report_form=create_report_form)
    return JSONResponse(status_code=status, content=msg)


@router.get("/{report_id}/download")
async def download_report(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    report_id: str,
    format: str,
    acunetix_id: str,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    filename, data = await acunetix_service.get_report_file(project_id=project_id, acunetix_id=acunetix_id, report_id=report_id, format=format)
    if format == "pdf":
        content_type = "application/pdf"
    else:
        content_type = "text/html"
    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return Response(content=data, headers=headers, media_type=content_type)


@router.get("/templates")
async def get_reports_templates(
    acunetix_service: Annotated[AcunetixService, Depends(AcunetixService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
):
    return await acunetix_service.get_report_templates(project_id=project_id)