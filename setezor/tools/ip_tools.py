import socket
import ipaddress

def is_ip_address(address):
        try:
            socket.inet_aton(address)
            return True
        except OSError:
            return False


def get_network(ip: str, mask: int) -> tuple[str:, str]:
    """ Функция получения инвормации о подсети по ip и маске

    Returns:
        tuple: (start_ip, broadcast)
    """

    network = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
    start_ip = str(network.network_address)
    broadcast = str(network.broadcast_address)
    return start_ip, broadcast