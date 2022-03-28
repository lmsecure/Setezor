# from database.db_connection import session_decorator
from sqlalchemy.orm.session import Session as session
from sqlalchemy.exc import OperationalError
from database.models import MAC, IP, L3Link, Object, Port
import traceback
from exceptions.exception_logger import exception_decorator
from exceptions.loggers import LoggerNames, get_logger


logger = get_logger(LoggerNames.db)


def exc_commit(ses: session):
    try:
        ses.commit()
        return True
    except OperationalError:
        logger.error(f'Database "{ses.bind}" is readonly. Maybe you not have permissions to write data in database')
        ses.rollback()
        return False


class Mock:
    def __getattribute__(self, item):
        return None


# General methods
@exception_decorator(LoggerNames.db, False)
def edit(ses: session, cls, expression: tuple, to_update: dict):
    obj = ses.query(cls).filter(*expression).update(to_update)
    ses.commit()
    return True


# Queries to Object table
def get_or_add_object(ses: session, obj_type, os, status):
    ses.add(Object(object_type=obj_type, os=os, status=status))


# Queries to MAC table
@exception_decorator(LoggerNames.db, None)
def get_or_add_mac(ses: session, mac: str, **kwargs):
    mac_obj = ses.query(MAC).filter(MAC.mac == mac).first()
    tmp_mac_obj = MAC(mac=mac)
    if mac_obj:
        diff = mac_obj == tmp_mac_obj
        if diff:
            logger.debug(f'Find difference in MAC objects.\n'
                         f'OLD: mac: {mac_obj.mac}\n'
                         f'NEW: mac: {tmp_mac_obj.mac}\n'
                         f'DIFF: {diff}')
            edit(ses, MAC, (MAC.mac == mac,), diff)
    elif not mac_obj:
        mac_obj = tmp_mac_obj
        ses.add(mac_obj)
        logger.debug(f'Add new MAC object: {mac_obj.mac}')
    if not exc_commit(ses):
        return None
    return mac_obj


# Queries to IP table
@exception_decorator(LoggerNames.db, None)
def get_or_add_ip(ses: session, ip, mac=None, domain_name=None):
    ip_obj = ses.query(IP).filter(IP.ip == ip).first()
    mac_obj = get_or_add_mac(ses, mac) if mac else Mock()
    tmp_ip_obj = IP(ip=ip, mac_id=mac_obj.id, domain_name=domain_name)
    if ip_obj:
        diff = ip_obj == tmp_ip_obj
        if diff:
            logger.debug(f'Find difference in IP objects.\n'
                         f'OLD: ip: {ip_obj.ip}, mac: {ip_obj.mac.mac if ip_obj.mac else None}\n'
                         f'NEW: ip: {tmp_ip_obj.ip}, mac: {tmp_ip_obj.mac.mac if tmp_ip_obj.mac else None}\n'
                         f'DIFF: {diff}')
            edit(ses, IP, (IP.ip == ip,), diff)
    elif not ip_obj:
        ip_obj = tmp_ip_obj
        ses.add(ip_obj)
        logger.debug(f'Add new IP object: ip: {ip}, mac: {mac}')
    if not exc_commit(ses):
        return None
    return ip_obj


# Queries to L3Link table
@exception_decorator(LoggerNames.db, None)
def get_or_add_l3_link(ses: session, child_ip, parent_ip, child_mac=None, parent_mac=None, child_name=None, parent_name=None, **kwargs):
    child_obj = get_or_add_ip(ses, child_ip, child_mac, child_name)
    parent_obj = get_or_add_ip(ses, parent_ip, parent_mac, parent_name)
    link_obj = ses.query(L3Link).filter(L3Link.child_ip_id == child_obj.id, L3Link.parent_ip_id == parent_obj.id).first()
    if not link_obj:
        link_obj = L3Link(child_ip_id=child_obj.id, parent_ip_id=parent_obj.id)
        ses.add(link_obj)
        logger.debug(f'Add new L3LINK object: parent_ip: {parent_ip}, child_ip: {child_ip}')
    if not exc_commit(ses):
        return None
    return link_obj


@exception_decorator(LoggerNames.db, [])
def get_all_l3_links(ses: session):
    records = ses.query(L3Link).all()
    return records


def delete_link(ses: session, ):
    pass


# Queries to Port table
@exception_decorator(LoggerNames.db, None)
def get_or_add_port(ses: session, ip, port, mac=None, service=None, product=None, extra_info=None, version=None,
                    os_type=None, cpe=None, state=None, **kwargs):
    ip_obj = get_or_add_ip(ses, ip, mac)
    port_obj = ses.query(Port).filter(Port.ip == ip_obj, Port.port == port).first()
    tmp_port_obj = Port(ip_id=ip_obj.id, port=int(port), service_name=service, product=product, extra_info=extra_info, version=version,
                           os_type=os_type, cpe=cpe, state=state)
    if port_obj:
        diff = port_obj == tmp_port_obj
        if diff:
            logger.debug(f'Find difference in PORT objects.\n'
                         f'OLD: ip: {port_obj.ip.ip}, port: {port_obj.port}, service_name: {port_obj.service_name}, '
                         f'product: {port_obj.product}, extrainfo: {port_obj.extrainfo}, version: {port_obj.version}, '
                         f'os_type: {port_obj.os_type}, state: {port_obj.state}, cpe: {port_obj.cpe}\n'
                         f'NEW: ip: {ip}, port: {port}, service_name: {service}, product: {product}, '
                         f'extrainfo: {extra_info}, version: {version}, os_type: {os_type}, state: {state}, cpe: {cpe}\n'
                         f'DIFF: {diff}')
            edit(ses, Port, (Port.port == port, Port.ip_id == ip_obj.id), diff)
    elif not port_obj:
        port_obj = tmp_port_obj
        ses.add(port_obj)
        logger.debug(f'Add new PORT object: ip: {ip}, port: {port}, service_name: {service}, '
                     f'product: {product}, extrainfo: {extra_info}, version: {version}, '
                     f'os_type: {os_type}, state: {state}, cpe: {cpe}')
    if not exc_commit(ses):
        return None
    return port_obj
