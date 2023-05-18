from scan.passive_scan.sniffers import ARPSniffer
from scapy.all import srp
from scapy.layers.inet import Ether
from scapy.layers.l2 import ARP
from scapy.plist import PacketList


class ARPScanner:
    def __init__(self):
        pass

    def snan_by_arp(self, pdst: str, dst_mac='ff:ff:ff:ff:ff:ff'):
        ans, _ = srp(Ether(dst=dst_mac)/ARP(pdst=pdst), timeout=2)
        result = [r for s, r in ans]
        return ARPSniffer.parse_packets_list(PacketList(result))
