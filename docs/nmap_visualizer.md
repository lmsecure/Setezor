classDiagram
direction BT
class ABC
class Base
class Exception
class Timer
class node44 {
    engine
    Session
   __init__(self, db_path: str, create_tabels: bool=True) 
   create_session(self) 
}
class node21 {
    logger
   __eq__(self, other) 
   to_dict(self) 
}
class node27 {
    __tablename__
    id
    mac
    _mac
    ip
    domain_name
    _host_ip
   to_dict(self) 
}
class node30 {
    __tablename__
    id
    child_ip
    _child_ip
    parent_ip
    _parent_ip
   to_dict(self) 
}
class node56 {
    __tablename__
    id
    mac
    object
    _obj
    _ip
   to_dict(self) 
}
class node45 {
    __tablename__
    id
    object_type
    os
    status
    _mac
}
class node54 {
    __tablename__
    id
    ip
    _ip
    _screenshot
    port
    service_name
    state
    product
    extra_info
    version
    os_type
    cpe
   to_dict(self) 
}
class node23 {
    __tablename__
    id
    port
    _port
    screenshot_path
    task
    _task
    domain
   to_dict(self) 
}
class node43 {
    __tablename__
    id
    status
    created
    started
    finished
    params
    comment
}
class node46 {
    task
    port
    ip
    screenshot
    l3link
    db
    mac
    object
   __init__(self, db_path: str) 
}
class node20 {
    logger
    session_maker
    model
   __init__(self, session_maker: Session) 
   session_provide(func) 
   write(self, session: Session, ret: str=None, **kwargs) 
   write_many(self, session: Session, data: list) 
   create(self, session: Session, *args, **kwargs) 
   get_or_create(self, session, **kwargs) 
   get_all(self, session: Session, result_format: str='dict') 
   delete_by_id(self, session: Session, id: int) 
   get_headers(self, *args, **kwargs) 
   update(self, session: Session, expression: tuple, to_update: dict) 
}
class node1 {
   __getattribute__(self, item) 
}
class node5 {
    mac
    model
   __init__(self, mac: MACQueries, session_maker: Session) 
   create(self, session: Session, ip: str, mac: str=None, domain_name: str=None) 
}
class node11 {
    ip
    model
   __init__(self, ip: IPQueries, session_maker: Session) 
   create(self, session: Session, child_ip: str, parent_ip: str, child_mac: str=None, parent_mac: str=None,
                         child_name: str=None, parent_name: str=None, start_ip: str=None) 
   get_nodes_and_edges(self, session: Session) 
}
class node33 {
    object
    model
   __init__(self, objects: ObjectQueries, session_maker: Session) 
   create(self, session: Session, mac: str, **kwargs) 
}
class node3 {
    model
   create(self, session: Session, obj_type: str, os: str, status: str) 
}
class node36 {
    ip
    model
   __init__(self, ip: IPQueries, session_maker: Session) 
   create(self, session: Session, ip: str, port: int, mac: str=None, service: str=None, product: str=None,
                         extra_info: str=None, version: str=None, os_type: str=None, cpe: str=None, state: str=None, **kwargs) 
   get_ports_by_ip(self, session: Session, ip_id: int) 
}
class node48 {
    task
    port
    model
   __init__(self, task: TaskQueries, port: PortQueries, session_maker: Session) 
   create(self, session: Session, path: str, task_id: int, ip: str=None, port: int=None, domain: str=None) 
}
class node25 {
    model
   create(self, session: Session, status: str, params: dict) 
   set_pending_status(self, session: Session, index: int) 
   set_finished_status(self, session: Session, index: int) 
   set_failed_status(self, session: Session, index: int, error_message: str) 
   get_last_finished_tasks(self, session: Session, interval: int) 
   get_not_finished_tasks(self, session: Session) 
}
class node8 {
    main
    gui
    db
    scan
    screenshoter
    task
}
class node49 {
    message
   __init__(self, url: str, message: str) 
}
class node6 {
    message
   __init__(self, message: str) 
}
class node42 {
    message
   __init__(self) 
}
class node22 {
    message
   __init__(self, filepath: str) 
}
class node17 {
   execute_async(self, *args, **kwargs) 
   execute(self, *args, **kwargs) 
}
class node4 {
    parser
    scanner
   __init__(self) 
   execute(self, iface: str) 
   execute_async(self, iface: str) 
}
class node19 {
   to_list(data: dict or list) 
   parse_addresses(address: list or dict) 
   parse_hostname(hostnames: list or dict) 
   parse_traces(trace: list or dict, self_address: dict) 
   parse_ports(ports: dict or list, address: dict) 
   parse_hosts(self, scan: dict, self_address: dict) 
}
class node40 {
    addresses
    traces
    hostnames
    ports
    __slots__
   __init__(self) 
}
class node28 {
    start_command
    superuser_permision
   run(self, extra_args: str, _password: str) 
   async_run(self, extra_args: str, _password: str) 
   parse_xml(input_xml: str) 
   save_source_data(path: str, scan_xml: str, command: str) 
}
class node57 {
    nmap_logs
    project_path
    database_file
    project_name
    scapy_logs
    __dict__
    screenshots
    network_interface
   __init__(self, project_path: str, iface: str=None) 
   __generate_configs(self) 
   create_config_file(self, config_file_name: str=project_config_file_name) 
   load_config_from_file(self) 
   get_config_dict(self) 
}
class node59 {
    project_structure
   __init__(self, project_structure: dict) 
   create_project_structure(self) 
   check_project_structure(self) 
   __create_file_in_project_folder(self, path: list) 
   __create_folder_in_project_folder(self, path: list) 
   __check_path_in_project_folder(self, path: list) 
}
class node39 {
    projects_path
   __init__(self) 
   get_existing_projects_name(self) 
   create_project(self, project_name: str, iface: str) 
   delete_project(self, project_name: str) 
   get_project_config(self, project_name: str) 
}
class node35 {
   __init__(self) 
   snan_by_arp(self, pdst: str, dst_mac='ff:ff:ff:ff:ff:ff') 
}
class node52 {
   split_range(source_range: str) 
   to_list_by_netmask(ip_range: str) 
   to_list_by_dash(ip_range: str) 
   validate_range(ip_range: str) 
}
class node15 {
    chromium_path
    options
   __init__(self, chromium_path) 
   take_screenshot_by_ip_port(self, ip: str, port: int, file_path: str, file_name: str,) 
   take_screenshot_by_domain(self, domain: str, file_path: str, file_name: str,) 
}
class node24 {
   __init__(self, iface: str) 
   parse_packet(pkt: Packet) 
   parse_packets_list(self, pkt_list: PacketList) 
   is_packet_type(pkt: Packet) 
}
class node32 {
    iface
    sniffer
    logger
   __init__(self, iface: str, **kwargs) 
   execute(self, timeout: float) 
   execute_async(self, timeout: float) 
   start_sniffing(self) 
   stop_sniffing(self) 
   parse_packets_list(self, pkt_list: PacketList) 
   _parse_packet_list(self, pkt_list: PacketList) 
   read_pcap(path: str) 
   save_sniffing_as_pcap(self, path: str, pkt_list: PacketList, append: bool=True) 
   is_packet_type(pkt: Packet) 
   parse_packet(self, pkt: Packet) 
}
class node26 {
   __init__(self, iface: str) 
   parse_packet(pkt: Packet) 
   parse_packets_list(self, pkt_list: PacketList) 
   is_packet_type(pkt: Packet) 
}
class node29 {
   __init__(self, iface: str) 
   parse_packet(pkt: Packet) 
   parse_packets_list(self, pkt_list: PacketList) 
   is_packet_type(pkt: Packet) 
}
class node9 {
   __init__(self, iface: str) 
   parse_packet(pkt: Packet) 
   parse_packets_list(self, pkt_list: PacketList) 
   is_packet_type(pkt: Packet) 
}
class node12 {
    endpoint
    queries_path
   __init__(self, path: str) 
   route(method, path) 
   create_from_table(self, request: Request) 
   create(self, request: Request) 
   delete_by_id(self, request: Request) 
   update(self, request: Request) 
   update_from_table(self, request: Request) 
   get_all(self, request: Request) 
   get_db_queries(self, request: Request) 
}
class node34 {
    endpoint
    queries_path
}
class node53 {
    endpoint
    queries_path
   get_nodes_and_edges(self, request: Request) 
}
class node18 {
    endpoint
    queries_path
}
class node13 {
    endpoint
    queries_path
}
class node7 {
    endpoint
    queries_path
   get_port_by_ip(self, request: Request) 
   get_port_like_ip(self, request: Request) 
}
class node55 {
    endpoint
    queries_path
   create_from_table(self, request: Request) 
   create(self, request: Request) 
   delete_by_id(self, request: Request) 
   update(self, request: Request) 
   get_all(self, request: Request) 
   set_project(self, request: Request) 
   set_project_data_to_session(self, session: Session, project_name: str, app: Application) 
}
class node58 {
    endpoint
    queries_path
}
class node31 {
    endpoint
    queries_path
    tasks
   create(self, request: Request) 
   get_all(self, request: Request) 
   get_last_finished(self, request: Request) 
}
class node16 {
   _task_func(self, *args, **kwargs) 
   _write_result_to_db(self, *args, **kwargs) 
   execute(self, db: Queries, task_id: int, *args, **kwargs) 
}
class node50 {
   _task_func(self, xml_log: str, **kwargs) 
}
class node41 {
   _task_func(self, command: str, _password: str, **kwargs) 
   _write_result_to_db(self, db: Queries, result: list, iface:str, **kwargs) 
}
class node47 {
    task_type
   _task_func(iface: str, timeout: float) 
   _write_result_to_db(self, db: Queries, result: list, iface: str, *args, **kwargs) 
}
class node2 {
    task_type
   _task_func(ip: str, port: int, file_path: str, file_name: str, with_params: bool) 
   _write_result_to_db(self, db: Queries, task_id: int, params: dict, *args, **kwargs) 
}
class node10 {
    pending
    in_queue
    finished
    failed
}
class node51 {
    name
    instances
   __init__(self, name, *args, **kwargs) 
   run(self) 
   cancel_timer_by_name(cls, name: str) 
}

Base  -->  node27 
node21  -->  node27 
Base  -->  node30 
node21  -->  node30 
Base  -->  node56 
node21  -->  node56 
Base  -->  node45 
node21  -->  node45 
Base  -->  node54 
node21  -->  node54 
Base  -->  node23 
node21  -->  node23 
Base  -->  node43 
node21  -->  node43 
ABC  -->  node20 
node20  -->  node5 
node20  -->  node11 
node20  -->  node33 
node20  -->  node3 
node20  -->  node36 
node20  -->  node48 
node20  -->  node25 
Exception  -->  node49 
Exception  -->  node6 
Exception  -->  node42 
Exception  -->  node22 
ABC  -->  node17 
node17  -->  node4 
node32  -->  node24 
node17  -->  node32 
node32  -->  node26 
node32  -->  node29 
node32  -->  node9 
ABC  -->  node12 
node12  -->  node34 
node12  -->  node53 
node12  -->  node18 
node12  -->  node13 
node12  -->  node7 
node12  -->  node55 
node12  -->  node58 
node12  -->  node31 
ABC  -->  node16 
node41  -->  node50 
node16  -->  node41 
node16  -->  node47 
node16  -->  node2 
Timer  -->  node51 
