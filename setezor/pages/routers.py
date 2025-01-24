from setezor.pages.auth import router as router_auth
from setezor.pages.registration import router as router_registration
from setezor.pages.project_dashboard import router as router_dashboard
from setezor.pages.project import router as router_projects
from setezor.pages.network_map import router as router_network_map
from setezor.pages.tool import router as router_tool
from setezor.pages.vulnerabilities import router as router_vulnerabilities
from setezor.pages.info import router as router_info
from setezor.pages.settings import router as router_settings
from setezor.pages.scopes import router as router_scopes

pages_routers = [
    router_auth,
    router_registration,
    router_dashboard,
    router_projects,
    router_network_map,
    router_tool,
    router_vulnerabilities,
    router_info,
    router_settings,
    router_scopes,
]
