from setezor.api.tasks import router as router_tasks
from setezor.api.project import router as router_project
from setezor.api.auth import router as router_auth
from setezor.api.acunetix.acunetix import router as router_acunetix
from setezor.api.agents import router as router_agents
from setezor.api.vis import router as router_vis
from setezor.api.analytics import router as router_analytics
from setezor.api.l7 import router as router_resource
from setezor.api.l7_vulnerability import router as router_resource_vulnerability
from setezor.api.software import router as router_software
from setezor.api.vulnerability import router as router_vulnerability
from setezor.api.scan import router as router_scan
from setezor.api.scope import router as router_scope
from setezor.api.tasks_data import router as router_tasks_data


api_routers = [
    router_auth,
    router_project,
    router_tasks,
    router_acunetix,
    router_agents,
    router_vis,
    router_analytics,
    router_resource,
    router_resource_vulnerability,
    router_software,
    router_vulnerability,
    router_scan,
    router_scope,
    router_tasks_data
]
