
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from setezor.dependencies.project import get_current_project, role_required
from setezor.models import Scope, Target
from setezor.schemas.pagination import PaginatedResponse
from setezor.schemas.pagination import PaginatedResponse
from setezor.schemas.scope import ScopeCreateForm
from setezor.schemas.target import TargetCreate
from setezor.services import ScopeService, TargetService
from setezor.schemas.roles import Roles


router = APIRouter(
    prefix="/scope",
    tags=["Scope"],
)

@router.get("")
async def list_scopes(
    scope_service: Annotated[ScopeService, Depends(ScopeService.new_instance)],
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor, Roles.viewer]))
) -> list[Scope]:
    return await scope_service.list(project_id=project_id)

@router.post("", status_code=201)
async def create_scope(
    scope_service: Annotated[ScopeService, Depends(ScopeService.new_instance)],
    scope: ScopeCreateForm,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> Scope:
    return await scope_service.create(project_id=project_id, scope=scope)

@router.get("/{id}/targets")
async def get_scope_targets(
    scope_service: Annotated[ScopeService, Depends(ScopeService.new_instance)],
    id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    project_id: str = Depends(get_current_project)
) -> PaginatedResponse:
        result = await scope_service.get_filtred_targets(
        project_id=project_id, 
        id=id,
        page=page,
        limit=limit)
        return result

@router.delete("/{id}", status_code=204)
async def delete_scope_by_id(
    scope_service: Annotated[ScopeService, Depends(ScopeService.new_instance)],
    id: str,
):
    return await scope_service.delete_scope_by_id(id=id)

@router.post("/{id}/targets", status_code=201)
async def add_scope_targets(
    scope_service: Annotated[ScopeService, Depends(ScopeService.new_instance)],
    id: str,
    payload: TargetCreate,
    project_id: str = Depends(get_current_project),
    _: bool = Depends(role_required([Roles.owner, Roles.executor]))
) -> list[Target]:
    result =  await scope_service.create_targets(project_id=project_id, id=id, payload=payload)
    return result

@router.get("/{scope_id}/download")
async def download_scope(
    scope_service: Annotated[ScopeService, Depends(ScopeService.new_instance)],
    scope_id: str,
    project_id: str = Depends(get_current_project)
) -> bytes:
    file = await scope_service.get_csv_from_scope(project_id=project_id, scope_id=scope_id)
    return StreamingResponse(
        file,
        media_type="application/csv"
        )