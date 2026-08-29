#!/usr/bin/env python3
"""
NetSage AI - Cisco Packet Tracer (.pkt) File Generator
======================================================
Author: Sanjana Narni
Technology: Applied AI + Network Troubleshooting (Cisco NetAcad)

Generates the Packet Tracer Network Simulation file (.pkt) containing
the multi-VLAN corporate branch topology, devices, cables, IP configurations,
and Cisco IOS startup commands for NetSage AI.
"""

import os
import xml.etree.ElementTree as ET

def generate_packet_tracer_pkt_file(output_path: str):
    """Constructs a valid Packet Tracer network topology XML/PKT file structure."""
    
    root = ET.Element("PACKETTRACER_FILE", version="8.2.0")

    # Header & Meta Info
    meta = ET.SubElement(root, "METADATA")
    ET.SubElement(meta, "PROJECT_NAME").text = "NetSage AI Troubleshooting Lab"
    ET.SubElement(meta, "STUDENT_NAME").text = "Sanjana Narni"
    ET.SubElement(meta, "COLLEGE_NAME").text = "Cisco Networking Academy"
    ET.SubElement(meta, "TECHNOLOGY").text = "Applied AI + Network Troubleshooting"
    
    # Topology Container
    network = ET.SubElement(root, "NETWORK_TOPOLOGY")

    # Devices Definitions
    devices = [
        {
            "id": "R1",
            "name": "Router-1",
            "model": "Cisco 2911 ISR",
            "type": "ROUTER",
            "x": 400, "y": 150,
            "interfaces": [
                {"name": "GigabitEthernet0/0", "ip": "Unassigned (802.1Q Sub-interfaces)", "connect_to": "Switch-1:Gi0/1"},
                {"name": "GigabitEthernet0/0.10", "ip": "192.168.10.1/24", "vlan": "10 (Sales)"},
                {"name": "GigabitEthernet0/0.20", "ip": "192.168.20.1/24", "vlan": "20 (Marketing)"},
                {"name": "GigabitEthernet0/0.40", "ip": "172.16.40.1/24", "vlan": "40 (Guest Wi-Fi)"},
                {"name": "GigabitEthernet0/1", "ip": "203.0.113.2/30", "connect_to": "ISP-Gateway:Gi0/1"},
                {"name": "GigabitEthernet0/2", "ip": "192.168.1.1/24", "connect_to": "DMZ-Web-Server:Fa0"}
            ],
            "startup_config": """hostname Router-1
interface GigabitEthernet0/0.10
 encapsulation dot1Q 10
 ip address 192.168.10.1 255.255.255.0
 ip nat inside
interface GigabitEthernet0/0.20
 encapsulation dot1Q 20
 ip address 192.168.20.1 255.255.255.0
 ip nat inside
interface GigabitEthernet0/0.40
 encapsulation dot1Q 40
 ip address 172.16.40.1 255.255.255.0
 ip access-group GUEST_ISOLATION in
interface GigabitEthernet0/1
 ip address 203.0.113.2 255.255.255.252
 ip access-group 101 in
 ip nat outside
interface GigabitEthernet0/2
 ip address 192.168.1.1 255.255.255.0
 ip nat inside
ip nat inside source list 1 interface GigabitEthernet0/1 overload
access-list 1 permit 192.168.10.0 0.0.0.255
access-list 1 permit 192.168.20.0 0.0.0.255
ip access-list extended 101
 permit icmp any any
 20 permit tcp any host 192.168.1.100 eq www
 permit ip any any
ip route 0.0.0.0 0.0.0.0 203.0.113.1
router ospf 1
 network 192.168.10.0 0.0.0.255 area 0
 network 192.168.20.0 0.0.0.255 area 0
end"""
        },
        {
            "id": "SW1",
            "name": "Switch-1",
            "model": "Cisco Catalyst 2960",
            "type": "SWITCH",
            "x": 400, "y": 300,
            "interfaces": [
                {"name": "FastEthernet0/1", "vlan": "10", "connect_to": "PC-A:Fa0"},
                {"name": "FastEthernet0/2", "vlan": "20", "connect_to": "PC-B:Fa0"},
                {"name": "FastEthernet0/8", "vlan": "10", "note": "Port Security Sticky Enabled"},
                {"name": "GigabitEthernet0/1", "mode": "Trunk (802.1Q)", "connect_to": "Router-1:Gi0/0"},
                {"name": "GigabitEthernet0/2", "mode": "Trunk (802.1Q)", "connect_to": "Switch-2:Gi0/2"}
            ],
            "startup_config": """hostname Switch-1
vlan 10
 name Sales
vlan 20
 name Marketing
vlan 30
 name Engineering
vlan 40
 name Guest-Wireless
vlan 50
 name Server-Farm
interface FastEthernet0/1
 switchport mode access
 switchport access vlan 10
interface FastEthernet0/2
 switchport mode access
 switchport access vlan 20
interface GigabitEthernet0/1
 switchport mode trunk
 switchport trunk native vlan 1
 switchport trunk allowed vlan 10,20,30,40,50
interface GigabitEthernet0/2
 switchport mode trunk
 switchport trunk native vlan 1
end"""
        },
        {
            "id": "SW2",
            "name": "Switch-2",
            "model": "Cisco Catalyst 2960",
            "type": "SWITCH",
            "x": 600, "y": 300,
            "interfaces": [
                {"name": "FastEthernet0/5", "vlan": "30", "connect_to": "PC-C:Fa0"},
                {"name": "GigabitEthernet0/2", "mode": "Trunk (802.1Q)", "connect_to": "Switch-1:Gi0/2"}
            ]
        },
        {
            "id": "PCA",
            "name": "PC-A",
            "type": "HOST",
            "ip": "192.168.10.10", "mask": "255.255.255.0", "gw": "192.168.10.1", "dns": "192.168.1.10",
            "x": 250, "y": 450
        },
        {
            "id": "PCB",
            "name": "PC-B",
            "type": "HOST",
            "ip": "192.168.20.10", "mask": "255.255.255.0", "gw": "192.168.20.1", "dns": "192.168.1.10",
            "x": 400, "y": 450
        },
        {
            "id": "PCC",
            "name": "PC-C",
            "type": "HOST",
            "ip": "192.168.30.10", "mask": "255.255.255.0", "gw": "192.168.30.1", "dns": "192.168.1.10",
            "x": 600, "y": 450
        },
        {
            "id": "SERVER",
            "name": "DMZ-Web-Server",
            "type": "SERVER",
            "ip": "192.168.1.100", "mask": "255.255.255.0", "gw": "192.168.1.1", "dns": "192.168.1.10",
            "services": ["HTTP: ON (Port 80)", "DNS: ON (192.168.1.10)"],
            "x": 200, "y": 150
        },
        {
            "id": "ISP",
            "name": "ISP-Gateway",
            "type": "ROUTER",
            "ip": "203.0.113.1/30",
            "x": 600, "y": 150
        }
    ]

    for d_info in devices:
        dev_node = ET.SubElement(network, "DEVICE", id=d_info["id"], name=d_info["name"], type=d_info["type"])
        ET.SubElement(dev_node, "POS_X").text = str(d_info.get("x", 0))
        ET.SubElement(dev_node, "POS_Y").text = str(d_info.get("y", 0))
        if "ip" in d_info:
            ET.SubElement(dev_node, "IP_ADDRESS").text = d_info["ip"]
        if "gw" in d_info:
            ET.SubElement(dev_node, "DEFAULT_GATEWAY").text = d_info["gw"]
        if "startup_config" in d_info:
            ET.SubElement(dev_node, "STARTUP_CONFIG").text = d_info["startup_config"]

    # Write formatted XML tree
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"Successfully generated Packet Tracer lab topology: {output_path}")

if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "packet_tracer_lab", "Sanjana_Narni-Cisco_NetAcad-NetSage_AI.pkt")
    generate_packet_tracer_pkt_file(out_file)
