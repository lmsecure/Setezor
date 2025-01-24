
from setezor.pages import TEMPLATES_DIR
from setezor.services import ObjectTypeService
from setezor.managers import ProjectManager
from setezor.tools.ip_tools import get_interfaces
from setezor.tools.acunetix import acunetix_groups_context,acunetix_targets_context,\
                                   acunetix_scans_context,acunetix_reports_context
from setezor.api.dependencies import UOWDep
from setezor.dependencies.project import get_current_project
from setezor.modules.wappalyzer.wappalyzer import WappalyzerParser
from fastapi import APIRouter, Request, Depends


router = APIRouter(tags=["Tools"])

@router.get("/tools")
async def network_page(
    request: Request,
    uow: UOWDep,
    project_id: str = Depends(get_current_project)
):
    """Формирует html страницу отображения топологии сети на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    #is_scapy_running = project.schedulers.get('scapy').active_count
    device_types = [{'label': i.name.capitalize(), 'value': i.name} for i in (await ObjectTypeService.list(uow=uow)) ]
    project = await ProjectManager.get_by_id(uow=uow, project_id=project_id)
    context = {"request": request,
               "project": project,
               'device_types': device_types,
               'is_scapy_running': False,
               'current_project': project.name,
               'current_project_id': project.id}
    
    context.update(acunetix_groups_context())
    context.update(acunetix_targets_context())
    context.update(acunetix_scans_context())
    #context.update(await acunetix_reports_context(project.configs.files.acunetix_configs))
    context.update(await acunetix_reports_context())
    context.update({'wappalyzer_groups' : WappalyzerParser.get_groups(), 'wappalyzer_name_categories_by_group' : WappalyzerParser.get_categories_by_group()})
    return TEMPLATES_DIR.TemplateResponse(name="network/tool_base.html", context=context)


