import uuid
from sqlmodel import SQLModel
from .base import Base, TimeDependent,IDDependent, ProjectDependent
from .d_object_type import ObjectType
from .object import Object
from .mac import MAC
from .agent import Agent
from .ip import IP
from .network import Network
from .d_network_type import Network_Type
from .asn import ASN
from .port import Port
from .domain import Domain
from .dns_a import DNS_A
from .dns_cname import DNS_CNAME
from .dns_mx import DNS_MX
from .dns_ns import DNS_NS
from .dns_txt import DNS_TXT
from .dns_soa import DNS_SOA
from .task import Task
from .route import Route
from .route_list import RouteList
from .project import Project
from .l4_software_vulnerability_screenshot import L4SoftwareVulnerabilityScreenshot
from .screenshot import Screenshot
from .d_vendor import Vendor
from .d_software import Software
from .d_software_type import SoftwareType
from .d_software_version import SoftwareVersion

from .vulnerability import Vulnerability
from .acunetix import Acunetix
from .whois_ip import WhoIsIP
from .whois_domain import WhoIsDomain
from .certificate import Cert
from .auth_credentials_resource import Authentication_Credentials
from .user import User
from .user_project import UserProject
from .scope import Scope
from .target import Target
from .organization import Organization
from .department import Department
from .object_employee import Object_Employee
from .employee import Employee
from .phone import Phone
from .employee_phone import Employee_Phone
from .email import Email
from .employee_email import Employee_Email
from .d_hardware import Hardware
from .d_hardware_type import Hardware_Type
from .scan import Scan
from .role import Role
from .auth_log import AuthLog
from .l4_software import L4Software
from .l4_software_vulnerability import L4SoftwareVulnerability
from .vulnerability_link import VulnerabilityLink
from .invite_link import Invite_Link
from .node_comment import NodeComment
from .l4_software_vulnerability_comment import L4SoftwareVulnerabilityComment
from .settings import Settings
from .agent_in_project import AgentInProject
from .agent_parent_agent import AgentParentAgent
from .network_speed_test import NetworkSpeedTest


def get_model_by_name(model_name:str):
    model_class = globals().get(model_name)
    
    if model_class and issubclass(model_class, SQLModel):
        return model_class
    else:
        raise ValueError(f"Модель с именем {model_name} не найдена или не является SQLModel.")