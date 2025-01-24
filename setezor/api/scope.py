
from fastapi import APIRouter, Depends
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project
from setezor.models import Scope, Target
from setezor.schemas.scope import ScopeCreateForm
from setezor.schemas.target import TargetCreate
from setezor.services import ScopeService, TargetService

router = APIRouter(
    prefix="/scope",
    tags=["Scope"],
)

@router.get("")
async def list_scopes(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list[Scope]:
    return await ScopeService.list(uow=uow, project_id=project_id)

@router.post("")
async def create_scope(
    uow: UOWDep,
    scope: ScopeCreateForm,
    project_id: str = Depends(get_current_project)
) -> Scope:
    return await ScopeService.create(uow=uow, project_id=project_id, scope=scope)

@router.get("/{id}/targets")
async def get_scope_targets(
    uow: UOWDep,
    id: str,
    project_id: str = Depends(get_current_project)
) -> list[Target]:
    return await ScopeService.get_targets(uow=uow, project_id=project_id, id=id)

@router.post("/{id}/add_targets")
async def add_scope_targets(
    uow: UOWDep,
    id: str,
    payload: TargetCreate,
    project_id: str = Depends(get_current_project)
) -> list[Target]:
    return await ScopeService.create_targets(uow=uow, project_id=project_id, id=id, payload=payload)

@router.get("/cert_data")
async def get_cert_data_targets(
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
) -> list:
    return await TargetService.get_transform_cert_scope_data(uow=uow, project_id=project_id)