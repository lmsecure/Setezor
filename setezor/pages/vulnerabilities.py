
from setezor.pages import TEMPLATES_DIR
from setezor.services import ObjectTypeService
from setezor.managers import ProjectManager
from setezor.tools.ip_tools import get_interfaces
from setezor.tools.acunetix import acunetix_groups_context, acunetix_targets_context, \
    acunetix_scans_context, acunetix_reports_context
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project
from setezor.modules.wappalyzer.wappalyzer import WappalyzerParser
from fastapi import APIRouter, Request, Depends


router = APIRouter(tags=["Vulnerabilities"])

@router.get("/vulnerabilities")
async def vulnerabilities_page(
    request: Request,
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
):
    """Формирует html страницу отображения информации из базы на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    project = await ProjectManager.get_by_id(uow=uow, project_id=project_id)
    project_name = project.name
    project_id = project.id
    context = {
        "request":request,
        "tab": {
            'name': 'resource_vulnerabilities',
            "base_url": "/api/v1/resource",
            'columns': [
                {'field': 'id', 'title': 'ID'},
                {'field': 'ip', 'title': 'IP'},
                {'field': 'port', 'title': 'PORT'},
                {'field': 'domain', 'title': 'DOMAIN'},
            ]
        },
        'current_project': project_name, 
        'current_project_id': project_id,
    }
    return TEMPLATES_DIR.TemplateResponse(name="vulnerabilities.html", context=context)
