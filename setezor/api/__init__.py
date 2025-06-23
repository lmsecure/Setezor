from setezor.api.tasks import router as router_tasks
from setezor.api.project import router as router_project
from setezor.api.auth import router as router_auth
from setezor.api.acunetix.acunetix import router as router_acunetix
from setezor.api.agents import router as router_agents
from setezor.api.agents_in_project import router as router_agents_in_project
from setezor.api.vis import router as router_vis
from setezor.api.analytics import router as router_analytics
from setezor.api.l4 import router as router_l4
from setezor.api.l4_vulnerability import router as router_l4_vulnerability
from setezor.api.software import router as router_software
from setezor.api.vulnerability import router as router_vulnerability
from setezor.api.scan import router as router_scan
from setezor.api.scope import router as router_scope
from setezor.api.tasks_data import router as router_tasks_data
from setezor.api.user import router as router_user
from setezor.api.user_project import router as router_user_project
from setezor.api.target import router as router_target
from setezor.api.role import router as router_role
from setezor.api.settings import router as settings_router


api_routers = [
    router_auth,
    router_project,
    router_tasks,
    router_acunetix,
    router_agents,
    router_agents_in_project,
    router_vis,
    router_analytics,
    router_l4,
    router_l4_vulnerability,
    router_software,
    router_vulnerability,
    router_scan,
    router_scope,
    router_tasks_data,
    router_user,
    router_user_project,
    router_target,
    router_role,
    settings_router
]