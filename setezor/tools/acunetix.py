"""
    Вспомогательные функции, возвращающие контекст для табулятора
"""


from setezor.schemas.acunetix.schemes.target_config import ScanSpeedValues
from setezor.modules.acunetix.scan import Scan
from setezor.modules.acunetix.acunetix_config import Config
from setezor.modules.acunetix.report import Report


def acunetix_groups_context() -> dict:
    context = {'groups_tab': {'name': 'groups',
                              'base_url': f'/api/v1/acunetix/groups',
                              'columns': [{'field': 'acunetix_name', 'title': 'AcunetixName'},
                                          {'field': 'name', 'title': 'Group Name'},
                                          {'field': 'description',
                                              'title': 'Description'},
                                          {'field': 'target_count',
                                              'title': 'Target Count', 'headerSort': False}
                                          ]}}
    return context


def acunetix_targets_context() -> dict:
    context = {'targets_tab': {'name': 'targets',
                               'base_url': f'/api/v1/acunetix/targets',
                               'columns': [{'field': 'acunetix_name', 'title': 'AcunetixName'},
                                           {'field': 'address', 'title': 'Address'},
                                           # {'field': 'description','title': 'Description'},
                                           # {'field': 'last_scan_session_status','title': 'Last Scan Status'},
                                           {'field': 'proxy', 'title': 'Proxy'},
                                           {'field': 'cookies',
                                               'title': 'URL | Cookie', "width": 500},
                                           {'field': 'headers', 'title': 'Headers'}
                                           ]}}
    return context


def acunetix_scans_context() -> dict:
    context = {'scans_tab': {'name': 'scans',
                             'base_url': f'/api/v1/acunetix/scans',
                             'columns': [{'field': 'acunetix_name', 'title': 'AcunetixName'},
                                         {'field': 'target', 'title': 'Address',
                                             'formatter': 'link', 'headerSort': False},
                                         {'field': 'profile_name',
                                          'title': 'Scan Profile', 'headerSort': False},
                                         {'field': 'last_scan_session_status',
                                             'title': 'Last Scan Status', 'headerSort': False},
                                         {'field': 'start_date',
                                             'title': 'Start Date', 'headerSort': True}
                                         ]}}
    return context


async def acunetix_reports_context() -> dict:
    context = {'reports_tab': {'name': 'reports',
                               'base_url': f'/api/v1/acunetix/reports',
                               'columns': [{'field': 'acunetix_name', 'title': 'AcunetixName'},
                                   {'field': 'template_name', 'title': 'Report Template'},
                                           {'field': 'source.description',
                                               'title': 'Target'},
                                           {'field': 'generation_date',
                                               'title': 'Created On'},
                                           {'field': 'status', 'title': 'Status'}], }, }
    return context
