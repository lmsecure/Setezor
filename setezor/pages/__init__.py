from fastapi.templating import Jinja2Templates
from setezor.settings import TEMPLATES_DIR_PATH


TEMPLATES_DIR = Jinja2Templates(directory=TEMPLATES_DIR_PATH)

from setezor.pages.auth import router as router_auth
from setezor.pages.registration import router as router_registration
from setezor.pages.project_dashboard import router as router_dashboard
from setezor.pages.project import router as router_projects
from setezor.pages.network_map import router as router_network_map
from setezor.pages.tool import router as router_tool
from setezor.pages.vulnerabilities import router as router_vulnerabilities
from setezor.pages.info import router as router_info
from setezor.pages.project_settings import router as router_project_settings
from setezor.pages.application_settings import router as router_application_settings
from setezor.pages.user_settings import router as router_user_settings
from setezor.pages.scopes import router as router_scopes
from setezor.pages.admin_settings import router as router_admin_settings

pages_routers = [
    router_auth,
    router_registration,
    router_dashboard,
    router_projects,
    router_network_map,
    router_tool,
    router_vulnerabilities,
    router_info,
    router_application_settings,
    router_project_settings,
    router_user_settings,
    router_scopes,
    router_admin_settings,
]