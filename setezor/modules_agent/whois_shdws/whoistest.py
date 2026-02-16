import socket
from ipaddress import ip_address, AddressValueError

class WhoisShdws:

    @classmethod
    def get_whois(cls, ip: str):
        try:
            ip_address(ip)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect(("asn.shadowserver.org", 43))
            s.send(f"origin {ip}\r\n".encode())
            response = b""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                response += data
            s.close()

            line = response.decode().strip()

            parts = line.split(" | ")
            if len(parts) == 5:
                return {
                    "OrgName": parts[4],
                    "Country": parts[3],
                    "ASN": parts[0],
                    "NetName": parts[2],
                    "CIDR": parts[1]
                }
            else:
                return {"raw": line}

        except AddressValueError:
            print("IP-address not valid")
        except ConnectionResetError as ex:
            print(ex)