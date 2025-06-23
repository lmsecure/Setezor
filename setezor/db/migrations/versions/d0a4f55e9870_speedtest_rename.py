"""speedtest+rename

Revision ID: d0a4f55e9870
Revises: 1bb9a386a83d
Create Date: 2025-06-19 11:25:07.114333

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd0a4f55e9870'
down_revision: Union[str, None] = '1bb9a386a83d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.rename_table("d_object_type", "setezor_d_object_type")
    op.rename_table("mac", "network_mac")
    op.rename_table("agent", "setezor_agent")
    op.rename_table("ip", "network_ip")
    op.rename_table("d_network_type", "setezor_d_network_type")
    op.rename_table("asn", "network_asn")
    op.rename_table("port", "network_port")
    op.rename_table("domain", "network_domain")
    op.rename_table("dns_a", "network_dns_a")
    op.rename_table("dns_cname", "network_dns_cname")
    op.rename_table("dns_mx", "network_dns_mx")
    op.rename_table("dns_ns", "network_dns_ns")
    op.rename_table("dns_txt", "network_dns_txt")
    op.rename_table("dns_soa", "network_dns_soa")
    op.rename_table("task", "project_task")
    op.rename_table("route", "network_route")
    op.rename_table("route_list", "network_route_list")
    op.rename_table("l4_software_vulnerability_screenshot", "network_port_software_vulnerability_screenshot")
    op.rename_table("screenshot", "software_web_screenshot")
    op.rename_table("d_vendor", "setezor_d_vendor")
    op.rename_table("d_software", "setezor_d_software")
    op.rename_table("d_software_type", "setezor_d_software_type")
    op.rename_table("d_software_version", "setezor_d_software_version")
    op.rename_table("vulnerability", "software_vulnerability")
    op.rename_table("acunetix", "setezor_tools_acunetix")
    op.rename_table("whois_ip", "software_web_whois_ip")
    op.rename_table("whois_domain", "software_web_whois_domain")
    op.rename_table("cert", "network_cert")
    op.rename_table("authentication_credentials", "software_authentication_credentials")
    op.rename_table("scope", "project_scope")
    op.rename_table("target", "project_scope_targets")
    op.rename_table("department", "organization_department")
    op.rename_table("phone", "organization_phone")
    op.rename_table("email", "organization_email")
    op.rename_table("d_hardware", "setezor_d_hardware")
    op.rename_table("d_hardware_type", "setezor_d_hardware_type")
    op.rename_table("scan", "project_scan")
    op.rename_table("role", "user_role")
    op.rename_table("auth_log", "user_auth_log")
    op.rename_table("l4_software", "network_port_software")
    op.rename_table("l4_software_vulnerability", "network_port_software_vulnerability")
    op.rename_table("vulnerability_link", "software_vulnerability_link")
    op.rename_table("invite_link", "user_invite_link")
    op.rename_table("node_comment", "network_ip_node_comment")
    op.rename_table("l4_software_vulnerability_comment", "network_port_software_vulnerability_comment")
    op.rename_table("settings", "setezor_settings")
    op.rename_table("agent_in_project", "setezor_agent_in_project")
    op.rename_table("agent_parent_agent", "setezor_agent_parent_agent")

    # Index renames
    op.execute("ALTER INDEX ix_d_vendor_name RENAME TO ix_setezor_d_vendor_name")
    op.execute("ALTER INDEX ix_d_software_product RENAME TO ix_setezor_d_software_product")
    op.execute("ALTER INDEX ix_d_software_version_build RENAME TO ix_setezor_d_software_version_build")
    op.execute("ALTER INDEX ix_d_software_version_cpe23 RENAME TO ix_setezor_d_software_version_cpe23")
    op.execute("ALTER INDEX ix_d_software_version_version RENAME TO ix_setezor_d_software_version_version")
    op.execute("ALTER INDEX ix_mac_mac RENAME TO ix_network_mac_mac")
    op.execute("ALTER INDEX ix_ip_ip RENAME TO ix_network_ip_ip")
    op.execute("ALTER INDEX ix_port_port RENAME TO ix_network_port_port")
    op.execute("ALTER INDEX ix_domain_domain RENAME TO ix_network_domain_domain")
    op.execute("ALTER INDEX ix_invite_link_token_hash RENAME TO ix_user_invite_link_token_hash")


    op.create_table('network_speed_test',
    sa.Column('project_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True, comment='Идентификатор проекта'),
    sa.Column('created_by', sqlmodel.sql.sqltypes.AutoString(), nullable=True, comment='Задача, породившая сущность'),
    sa.Column('created_at', sa.DateTime(), nullable=False, comment='Дата-время создания сущности'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='Дата-время изменения сущности'),
    sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='Дата-время удаления сущности'),
    sa.Column('scan_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True, comment='Идентификатор скана'),
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('ip_id_from', sqlmodel.sql.sqltypes.AutoString(), nullable=False, comment='Идентификатор интерфейса с которого отправлялись пакеты'),
    sa.Column('ip_id_to', sqlmodel.sql.sqltypes.AutoString(), nullable=False, comment='Идентификатор интерфейса на который отправлялись пакеты'),
    sa.Column('speed', sa.Float(), nullable=False),
    sa.Column('port', sa.Integer(), nullable=False, comment='Номер порта на котором происходил замер'),
    sa.Column('protocol', sqlmodel.sql.sqltypes.AutoString(), nullable=False, comment='Протокол на котором происходил замер'),
    sa.ForeignKeyConstraint(['ip_id_from'], ['network_ip.id'], ),
    sa.ForeignKeyConstraint(['ip_id_to'], ['network_ip.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['scan_id'], ['project_scan.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='Таблица предназначена для хранения замеренной пропускной способности между машинами (агентами)'
    )
    op.create_index(op.f('ix_network_speed_test_port'), 'network_speed_test', ['port'], unique=False)




def downgrade():
    op.rename_table("setezor_d_object_type", "d_object_type")
    op.rename_table("network_mac", "mac")
    op.rename_table("setezor_agent", "agent")
    op.rename_table("network_ip", "ip")
    op.rename_table("setezor_d_network_type", "d_network_type")
    op.rename_table("network_asn", "asn")
    op.rename_table("network_port", "port")
    op.rename_table("network_domain", "domain")
    op.rename_table("network_dns_a", "dns_a")
    op.rename_table("network_dns_cname", "dns_cname")
    op.rename_table("network_dns_mx", "dns_mx")
    op.rename_table("network_dns_ns", "dns_ns")
    op.rename_table("network_dns_txt", "dns_txt")
    op.rename_table("network_dns_soa", "dns_soa")
    op.rename_table("project_task", "task")
    op.rename_table("network_route", "route")
    op.rename_table("network_route_list", "route_list")
    op.rename_table("network_port_software_vulnerability_screenshot", "l4_software_vulnerability_screenshot")
    op.rename_table("software_web_screenshot", "screenshot")
    op.rename_table("setezor_d_vendor", "d_vendor")
    op.rename_table("setezor_d_software", "d_software")
    op.rename_table("setezor_d_software_type", "d_software_type")
    op.rename_table("setezor_d_software_version", "d_software_version")
    op.rename_table("software_vulnerability", "vulnerability")
    op.rename_table("setezor_tools_acunetix", "acunetix")
    op.rename_table("software_web_whois_ip", "whois_ip")
    op.rename_table("software_web_whois_domain", "whois_domain")
    op.rename_table("network_cert", "cert")
    op.rename_table("software_authentication_credentials", "authentication_credentials")
    op.rename_table("project_scope", "scope")
    op.rename_table("project_scope_targets", "target")
    op.rename_table("organization_department", "department")
    op.rename_table("organization_phone", "phone")
    op.rename_table("organization_email", "email")
    op.rename_table("setezor_d_hardware", "d_hardware")
    op.rename_table("setezor_d_hardware_type", "d_hardware_type")
    op.rename_table("project_scan", "scan")
    op.rename_table("user_role", "role")
    op.rename_table("user_auth_log", "auth_log")
    op.rename_table("network_port_software", "l4_software")
    op.rename_table("network_port_software_vulnerability", "l4_software_vulnerability")
    op.rename_table("software_vulnerability_link", "vulnerability_link")
    op.rename_table("user_invite_link", "invite_link")
    op.rename_table("network_ip_node_comment", "node_comment")
    op.rename_table("network_port_software_vulnerability_comment", "l4_software_vulnerability_comment")
    op.rename_table("setezor_settings", "settings")
    op.rename_table("setezor_agent_in_project", "agent_in_project")
    op.rename_table("setezor_agent_parent_agent", "agent_parent_agent")

    # Index renames (downgrade)
    op.execute("ALTER INDEX ix_setezor_d_vendor_name RENAME TO ix_d_vendor_name")
    op.execute("ALTER INDEX ix_setezor_d_software_product RENAME TO ix_d_software_product")
    op.execute("ALTER INDEX ix_setezor_d_software_version_build RENAME TO ix_d_software_version_build")
    op.execute("ALTER INDEX ix_setezor_d_software_version_cpe23 RENAME TO ix_d_software_version_cpe23")
    op.execute("ALTER INDEX ix_setezor_d_software_version_version RENAME TO ix_d_software_version_version")
    op.execute("ALTER INDEX ix_network_mac_mac RENAME TO ix_mac_mac")
    op.execute("ALTER INDEX ix_network_ip_ip RENAME TO ix_ip_ip")
    op.execute("ALTER INDEX ix_network_port_port RENAME TO ix_port_port")
    op.execute("ALTER INDEX ix_network_domain_domain RENAME TO ix_domain_domain")
    op.execute("ALTER INDEX ix_user_invite_link_token_hash RENAME TO ix_invite_link_token_hash")


    op.drop_index(op.f('ix_network_speed_test_protocol'), table_name='network_speed_test')
    op.drop_index(op.f('ix_network_speed_test_port'), table_name='network_speed_test')
    op.drop_table('network_speed_test')
