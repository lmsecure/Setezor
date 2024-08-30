"""
    Вспомогательные функции, возвращающие контекст для табулятора
"""


from setezor.app_routes.api.acunetix.schemes.target_config import ScanSpeedValues
from setezor.modules.acunetix.scan import Scan
from setezor.modules.acunetix.acunetix_config import Config
from setezor.modules.acunetix.report import Report

def acunetix_groups_context() -> dict:
    context = {'groups_tab': {'name': 'groups',
                              'base_url': f'/api/acunetix/groups/',
                              'columns': [{'field': 'name', 'title': 'Group Name'},
                                          {'field': 'description',
                                              'title': 'Description'},
                                          {'field': 'target_count',
                                              'title': 'Target Count', 'headerSort': False}
                                          ]}}
    return context


def acunetix_targets_context() -> dict:
    context = {'targets_tab': {'name': 'targets',
                               'base_url': f'/api/acunetix/targets/',
                               'columns': [{'field': 'address', 'title': 'Address'},
                                           #{'field': 'description','title': 'Description'},
                                           #{'field': 'last_scan_session_status','title': 'Last Scan Status'},
                                           {'field': 'proxy','title': 'Proxy'},
                                           {'field': 'cookies','title': 'URL | Cookie',"width":500},
                                           {'field': 'headers','title': 'Headers'}
                                           ]}}
    return context


def acunetix_scans_context() -> dict:
    context = {'scans_tab': {'name': 'scans',
                             'base_url': f'/api/acunetix/scans/',
                             'columns': [{'field': 'target', 'title': 'Address', 'formatter': 'link','headerSort': False},
                                         {'field': 'profile_name',
                                          'title': 'Scan Profile','headerSort': False},
                                         {'field': 'last_scan_session_status','title': 'Last Scan Status','headerSort': False},
                                         {'field': 'start_date','title': 'Start Date','headerSort': False}
                                         ]}}
    return context


async def acunetix_reports_context(path) -> dict:
    context = {'reports_tab': {'name': 'reports',
                               'base_url': f'/api/acunetix/reports/',
                               'columns': [{'field': 'template_name', 'title': 'Report Template'},
                                           {'field': 'source.description',
                                               'title': 'Target'},
                                           {'field': 'generation_date',
                                               'title': 'Created On'},
                                           {'field': 'status', 'title': 'Status'}], }, }
    credentials = await Config.get(path)
    if not credentials:
        return context
    data = await Report.get_templates(credentials)
    context.update({"report_templates":data})
    return context

async def acunetix_scan_modal_context(path:str) -> dict:
    credentials = await Config.get(path)
    if not credentials:
        return {}
    data = await Scan.get_profiles(credentials)
    context = {"scanning_profiles":data}
    scan_speeds = [s.value for s in ScanSpeedValues]
    context.update({"scan_speeds":scan_speeds})
    return context