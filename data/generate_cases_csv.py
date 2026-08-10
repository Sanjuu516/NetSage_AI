import csv
import os

cases_data = [
    {
        "case_id": "CASE-01",
        "title": "Access Port in Wrong VLAN",
        "symptom": "PC-A in Sales cannot communicate with Sales Server on Switch-1 (192.168.10.50). PC gets static IP 192.168.10.10/24.",
        "topology_note": "PC-A connected to Switch-1 Fa0/1. Sales Server connected to Switch-1 Fa0/2. Sales VLAN is VLAN 10.",
        "show_outputs": """Switch-1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/3, Fa0/4, Fa0/5...
10   Sales                            active    Fa0/2
20   Marketing                        active    Fa0/1
Switch-1# show interfaces FastEthernet0/1 switchport
Name: Fa0/1
Administrative Mode: static access
Operational Mode: static access
Access Mode VLAN: 20 (Marketing)""",
        "expected_fault": "Interface FastEthernet0/1 is assigned to VLAN 20 (Marketing) instead of VLAN 10 (Sales)",
        "osi_layer": "Layer 2 - Data Link",
        "concept_tag": "VLAN",
        "severity": "High",
        "suggested_fix": """Switch-1(config)# interface FastEthernet0/1
Switch-1(config-if)# switchport access vlan 10
Switch-1(config-if)# end"""
    },
    {
        "case_id": "CASE-02",
        "title": "Missing VLAN in Switch Database",
        "symptom": "PC-1 in VLAN 30 cannot reach gateway or other VLAN 30 hosts across Switch-2.",
        "topology_note": "Switch-1 connected via Trunk (Gi0/1) to Switch-2. PC-1 connected to Switch-2 Fa0/5 in VLAN 30 (Engineering).",
        "show_outputs": """Switch-2# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/1, Fa0/2, Fa0/3, Fa0/4
10   Sales                            active    
20   Marketing                        active    
Switch-2# show interfaces FastEthernet0/5 switchport
Access Mode VLAN: 30 (Inactive)""",
        "expected_fault": "VLAN 30 is not created in Switch-2 VLAN database causing port Fa0/5 to become inactive",
        "osi_layer": "Layer 2 - Data Link",
        "concept_tag": "VLAN",
        "severity": "Critical",
        "suggested_fix": """Switch-2(config)# vlan 30
Switch-2(config-vlan)# name Engineering
Switch-2(config-vlan)# exit"""
    },
    {
        "case_id": "CASE-03",
        "title": "802.1Q Native VLAN Mismatch on Trunk",
        "symptom": "Intermittent connectivity between switches and CDP duplex/native VLAN mismatch syslog alerts logged every 60s.",
        "topology_note": "Switch-A (Gi0/1) connected to Switch-B (Gi0/1) via 802.1Q trunk cable.",
        "show_outputs": """Switch-A# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      10
Switch-B# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      1
%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/1 (1), with Switch-A GigabitEthernet0/1 (10).""",
        "expected_fault": "Native VLAN mismatch across trunk: Switch-A is configured with Native VLAN 10 while Switch-B is using Native VLAN 1",
        "osi_layer": "Layer 2 - Data Link",
        "concept_tag": "VLAN",
        "severity": "Medium",
        "suggested_fix": """Switch-B(config)# interface GigabitEthernet0/1
Switch-B(config-if)# switchport trunk native vlan 10
Switch-B(config-if)# end"""
    },
    {
        "case_id": "CASE-04",
        "title": "Trunk Allowed VLAN List Restricting Traffic",
        "symptom": "PC in VLAN 20 on Switch-2 cannot ping the Default Gateway (Router sub-interface) on Switch-1.",
        "topology_note": "Switch-1 Gi0/1 (Trunk) connects to Switch-2 Gi0/1 (Trunk). Router on a Stick connected to Switch-1.",
        "show_outputs": """Switch-1# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      1
Port        Vlans allowed on trunk
Gi0/1       10,30,40
Switch-2# show interfaces trunk
Port        Vlans allowed on trunk
Gi0/1       1-4094""",
        "expected_fault": "Trunk port Gi0/1 on Switch-1 is filtering out VLAN 20 from its allowed VLAN list",
        "osi_layer": "Layer 2 - Data Link",
        "concept_tag": "VLAN",
        "severity": "High",
        "suggested_fix": """Switch-1(config)# interface GigabitEthernet0/1
Switch-1(config-if)# switchport trunk allowed vlan add 20
Switch-1(config-if)# end"""
    },
    {
        "case_id": "CASE-05",
        "title": "Host Configured with Wrong Default Gateway",
        "symptom": "Host PC-3 (192.168.1.50/24) can ping local LAN hosts but cannot reach Internet server 8.8.8.8.",
        "topology_note": "Local LAN 192.168.1.0/24. Router LAN interface is 192.168.1.1/24.",
        "show_outputs": """PC-3> ipconfig
IP Address......................: 192.168.1.50
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.1.254
Router-1# show ip interface brief
Interface                  IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0         192.168.1.1     YES manual up                    up      
GigabitEthernet0/1         203.0.113.2     YES manual up                    up""",
        "expected_fault": "PC-3 has its Default Gateway configured as 192.168.1.254 instead of Router-1 IP 192.168.1.1",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "GATEWAY",
        "severity": "High",
        "suggested_fix": "PC-3> ipconfig 192.168.1.50 255.255.255.0 192.168.1.1"
    },
    {
        "case_id": "CASE-06",
        "title": "Subnet Mask Mismatch Between Host and Router",
        "symptom": "PC-B can ping some local hosts but cannot ping Router-1 gateway 10.0.10.1.",
        "topology_note": "LAN network is 10.0.10.0/24 (255.255.255.0). Router Gi0/0 is 10.0.10.1/24.",
        "show_outputs": """PC-B> ipconfig
IP Address......................: 10.0.10.75
Subnet Mask.....................: 255.255.255.128
Default Gateway.................: 10.0.10.1
Router-1# show ip interface GigabitEthernet0/0
GigabitEthernet0/0 is up, line protocol is up
  Internet address is 10.0.10.1/24""",
        "expected_fault": "PC-B subnet mask is set to 255.255.255.128 (/25) splitting the subnet and creating asymmetric reachability",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "GATEWAY",
        "severity": "Medium",
        "suggested_fix": "PC-B> ipconfig 10.0.10.75 255.255.255.0 10.0.10.1"
    },
    {
        "case_id": "CASE-07",
        "title": "Router-on-a-Stick Sub-interface Shutdown",
        "symptom": "VLAN 20 hosts can reach their gateway 192.168.20.1 but VLAN 10 hosts cannot reach 192.168.10.1.",
        "topology_note": "Router-1 connects to Switch-1 via 802.1Q sub-interfaces G0/0.10 and G0/0.20.",
        "show_outputs": """Router-1# show ip interface brief
Interface                  IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0         unassigned      YES unset  up                    up      
GigabitEthernet0/0.10      192.168.10.1    YES manual administratively down down    
GigabitEthernet0/0.20      192.168.20.1    YES manual up                    up""",
        "expected_fault": "Sub-interface GigabitEthernet0/0.10 is administratively shutdown on the router",
        "osi_layer": "Layer 1 - Physical",
        "concept_tag": "GATEWAY",
        "severity": "Critical",
        "suggested_fix": """Router-1(config)# interface GigabitEthernet0/0.10
Router-1(config-subif)# no shutdown
Router-1(config-subif)# end"""
    },
    {
        "case_id": "CASE-08",
        "title": "Duplicate IP Address on Local Segment",
        "symptom": "PC-1 experiences intermittent connectivity and receives 'IP Address Conflict Detected' warning.",
        "topology_note": "Subnet 192.168.1.0/24 with static servers and dynamic PCs.",
        "show_outputs": """Switch-1# show mac address-table dynamic
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
1       0001.9654.1111    DYNAMIC     Fa0/1
1       0001.9654.2222    DYNAMIC     Fa0/2
Router-1# show ip arp
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.20            0   0001.9654.1111  ARPA   GigabitEthernet0/0
Internet  192.168.1.20            0   0001.9654.2222  ARPA   GigabitEthernet0/0""",
        "expected_fault": "Duplicate IP address 192.168.1.20 is assigned to both PC-1 on Fa0/1 and a static network printer on Fa0/2",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "GATEWAY",
        "severity": "High",
        "suggested_fix": "PC-1> ipconfig 192.168.1.25 255.255.255.0 192.168.1.1"
    },
    {
        "case_id": "CASE-09",
        "title": "Missing IP Helper-Address for DHCP Relay",
        "symptom": "Clients in VLAN 10 (192.168.10.0/24) fail to obtain IP address and get APIPA 169.254.x.x.",
        "topology_note": "Central DHCP Server is located in Server Farm VLAN 50 (192.168.50.10). Router-1 is the gateway for VLAN 10.",
        "show_outputs": """PC-1> ipconfig /renew
DHCP client request failed.
IP Address: 169.254.34.12
Router-1# show run interface GigabitEthernet0/0.10
Building configuration...
interface GigabitEthernet0/0.10
 encapsulation dot1Q 10
 ip address 192.168.10.1 255.255.255.0
end""",
        "expected_fault": "Router sub-interface Gi0/0.10 is missing the 'ip helper-address 192.168.50.10' command to forward DHCP broadcasts",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "DHCP",
        "severity": "High",
        "suggested_fix": """Router-1(config)# interface GigabitEthernet0/0.10
Router-1(config-subif)# ip helper-address 192.168.50.10
Router-1(config-subif)# end"""
    },
    {
        "case_id": "CASE-10",
        "title": "DHCP Pool Excluded Address Overlap",
        "symptom": "DHCP server assigns default gateway IP 192.168.1.1 to a client PC causing network collapse.",
        "topology_note": "Router-1 acts as local DHCP Server for 192.168.1.0/24.",
        "show_outputs": """Router-1# show run | section ip dhcp
ip dhcp pool LAN-POOL
 network 192.168.1.0 255.255.255.0
 default-router 192.168.1.1
 dns-server 8.8.8.8
Router-1# show ip dhcp binding
IP address       Client-ID/Hardware address   Lease expiration        Type
192.168.1.1      0100.0c29.a45b.cd            Aug 10 2026 09:00 AM    Automatic""",
        "expected_fault": "Router DHCP pool configuration is missing 'ip dhcp excluded-address 192.168.1.1' so the gateway IP was leased",
        "osi_layer": "Layer 7 - Application",
        "concept_tag": "DHCP",
        "severity": "Critical",
        "suggested_fix": """Router-1(config)# ip dhcp excluded-address 192.168.1.1 192.168.1.10
Router-1(config)# clear ip dhcp binding 192.168.1.1"""
    },
    {
        "case_id": "CASE-11",
        "title": "Wrong Default-Router in DHCP Pool",
        "symptom": "All DHCP clients receive IP configuration but cannot access any external websites or servers.",
        "topology_note": "Router-1 DHCP pool configured for branch office subnet 172.16.10.0/24. Router IP is 172.16.10.1.",
        "show_outputs": """PC-1> ipconfig
IP Address......................: 172.16.10.15
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 172.16.10.254
Router-1# show run | section ip dhcp pool
ip dhcp pool BRANCH-POOL
 network 172.16.10.0 255.255.255.0
 default-router 172.16.10.254
 dns-server 8.8.8.8""",
        "expected_fault": "DHCP pool is configured with non-existent default-router 172.16.10.254 instead of 172.16.10.1",
        "osi_layer": "Layer 7 - Application",
        "concept_tag": "DHCP",
        "severity": "High",
        "suggested_fix": """Router-1(config)# ip dhcp pool BRANCH-POOL
Router-1(dhcp-config)# default-router 172.16.10.1
Router-1(dhcp-config)# end"""
    },
    {
        "case_id": "CASE-12",
        "title": "DHCP Snooping Untrusted Uplink Dropping DHCPOFFER",
        "symptom": "Switch-2 clients cannot obtain DHCP IP address from core switch DHCP server.",
        "topology_note": "Switch-2 connected to Switch-1 Core via Gi0/1. DHCP Snooping is enabled on Switch-2.",
        "show_outputs": """Switch-2# show ip dhcp snooping
Switch DHCP snooping is enabled
DHCP snooping is configured on following VLANs: 10,20
Interface                  Trusted    Rate limit (pps)
-------------------------- -------    ----------------
Switch-2# show ip dhcp snooping binding
(Empty)
%DHCP_SNOOPING-5-DHCP_PACKET_DROPPED: DHCP packet dropped on untrusted port GigabitEthernet0/1""",
        "expected_fault": "DHCP Snooping is enabled on Switch-2 but the uplink port Gi0/1 is untrusted, blocking DHCPOFFER packets",
        "osi_layer": "Layer 2 - Data Link",
        "concept_tag": "DHCP",
        "severity": "High",
        "suggested_fix": """Switch-2(config)# interface GigabitEthernet0/1
Switch-2(config-if)# ip dhcp snooping trust
Switch-2(config-if)# end"""
    },
    {
        "case_id": "CASE-13",
        "title": "DNS Server IP Misconfigured on Clients",
        "symptom": "Clients can ping public IP 8.8.8.8 and 192.168.1.1 but cannot open 'cisco.lab' or 'google.com' in browser.",
        "topology_note": "Internal DNS server is at 192.168.1.10. PC is configured with DNS 192.168.1.100.",
        "show_outputs": """PC-1> ping 192.168.1.10
Reply from 192.168.1.10: bytes=32 time<1ms TTL=128
PC-1> nslookup cisco.lab
*** Can't find cisco.lab: No response from server
PC-1> ipconfig
DNS Servers.....................: 192.168.1.100""",
        "expected_fault": "Client PC-1 has its DNS server set to 192.168.1.100 (non-existent) instead of 192.168.1.10",
        "osi_layer": "Layer 7 - Application",
        "concept_tag": "DNS",
        "severity": "High",
        "suggested_fix": "PC-1> ipconfig /dns 192.168.1.10"
    },
    {
        "case_id": "CASE-14",
        "title": "DNS Service Disabled on Target Server",
        "symptom": "PC cannot resolve hostname 'server.company.local' despite correct DNS server IP 10.1.1.5.",
        "topology_note": "DNS Server is a Cisco Packet Tracer Generic Server at 10.1.1.5.",
        "show_outputs": """PC-1> nslookup server.company.local
Server: 10.1.1.5
*** Request to 10.1.1.5 timed-out
DNS-Server# show services
Service       Status
HTTP          ON
DHCP          OFF
DNS           OFF
SYSLOG        ON""",
        "expected_fault": "DNS service is turned OFF on the server appliance at 10.1.1.5",
        "osi_layer": "Layer 7 - Application",
        "concept_tag": "DNS",
        "severity": "Medium",
        "suggested_fix": "DNS-Server> Turn ON DNS service in Server Services Tab -> Add A record for server.company.local -> 10.1.1.50"
    },
    {
        "case_id": "CASE-15",
        "title": "Missing Default Route on Edge Router",
        "symptom": "Branch router LAN can ping local router interfaces but cannot reach any Internet or HQ IPs.",
        "topology_note": "Branch-R1 connected to ISP-R1 via serial link 203.0.113.0/30 (Branch is .2, ISP is .1).",
        "show_outputs": """Branch-R1# show ip route
Codes: L - local, C - connected, S - static, R - RIP, O - OSPF
Gateway of last resort is not set
     172.16.0.0/16 is variably subnetted, 2 subnets, 2 masks
C       172.16.1.0/24 is directly connected, GigabitEthernet0/0
L       172.16.1.1/32 is directly connected, GigabitEthernet0/0
     203.0.113.0/30 is subnetted, 1 subnets
C       203.0.113.0/30 is directly connected, Serial0/0/0""",
        "expected_fault": "Branch router is missing a default static route ('ip route 0.0.0.0 0.0.0.0 203.0.113.1') toward ISP gateway",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "ROUTING",
        "severity": "Critical",
        "suggested_fix": """Branch-R1(config)# ip route 0.0.0.0 0.0.0.0 203.0.113.1
Branch-R1(config)# end"""
    },
    {
        "case_id": "CASE-16",
        "title": "OSPF Passive-Interface Configured on Inter-Router Link",
        "symptom": "R1 and R2 cannot form OSPF adjacency across Gi0/0 link; routes are not exchanged.",
        "topology_note": "R1 (10.0.0.1/30) connects to R2 (10.0.0.2/30) via Gi0/0. Both in OSPF area 0.",
        "show_outputs": """R1# show ip ospf neighbor
(Empty)
R1# show ip ospf interface GigabitEthernet0/0
GigabitEthernet0/0 is up, line protocol is up
  Internet Address 10.0.0.1/30, Area 0
  Process ID 1, Router ID 1.1.1.1, Network Type BROADCAST, Cost: 1
  No OSPF hello received
  Passive interface""",
        "expected_fault": "Interface GigabitEthernet0/0 is configured as passive-interface on R1 suppressing OSPF Hellos on the peer link",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "ROUTING",
        "severity": "High",
        "suggested_fix": """R1(config)# router ospf 1
R1(config-router)# no passive-interface GigabitEthernet0/0
R1(config-router)# end"""
    },
    {
        "case_id": "CASE-17",
        "title": "OSPF Area ID Mismatch Between Neighbors",
        "symptom": "R1 and R2 remain stuck in DOWN state and never form OSPF Full adjacency.",
        "topology_note": "R1 Gi0/1 (192.168.12.1/30) connects to R2 Gi0/1 (192.168.12.2/30).",
        "show_outputs": """R1# show run | section router ospf
router ospf 1
 network 192.168.12.0 0.0.0.3 area 0
R2# show run | section router ospf
router ospf 1
 network 192.168.12.0 0.0.0.3 area 1
R1# show log
%OSPF-4-ERRRCV: Received packet with invalid area ID 0.0.0.1 from 192.168.12.2 on GigabitEthernet0/1 (Area 0.0.0.0 expected)""",
        "expected_fault": "OSPF Area mismatch on interconnect link: R1 is in Area 0 while R2 is in Area 1",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "ROUTING",
        "severity": "High",
        "suggested_fix": """R2(config)# router ospf 1
R2(config-router)# no network 192.168.12.0 0.0.0.3 area 1
R2(config-router)# network 192.168.12.0 0.0.0.3 area 0
R2(config-router)# end"""
    },
    {
        "case_id": "CASE-18",
        "title": "OSPF MTU Mismatch Causing EXSTART/EXCHANGE State",
        "symptom": "OSPF neighbors R1 and R2 are stuck in EXSTART/EXCHANGE state and routing table never converges.",
        "topology_note": "R1 and R2 connected over GigabitEthernet0/1.",
        "show_outputs": """R1# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
2.2.2.2           1   EXSTART/DR      00:00:34    10.1.1.2        GigabitEthernet0/1
R1# show interfaces GigabitEthernet0/1 | include MTU
  MTU 1500 bytes, BW 1000000 Kbit/sec
R2# show interfaces GigabitEthernet0/1 | include MTU
  MTU 1400 bytes, BW 1000000 Kbit/sec""",
        "expected_fault": "MTU mismatch on GigabitEthernet0/1 link (R1=1500, R2=1400) preventing OSPF DBD packet exchange",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "ROUTING",
        "severity": "High",
        "suggested_fix": """R2(config)# interface GigabitEthernet0/1
R2(config-if)# ip mtu 1500
R2(config-if)# end"""
    },
    {
        "case_id": "CASE-19",
        "title": "Static Route Pointing to Invalid Next-Hop",
        "symptom": "HQ-Router cannot reach Remote Branch subnet 192.168.50.0/24.",
        "topology_note": "HQ-Router connected to Branch-Router (10.0.0.2/30) via Gi0/0 (10.0.0.1/30).",
        "show_outputs": """HQ-Router# show run | include ip route
ip route 192.168.50.0 255.255.255.0 10.0.0.6
HQ-Router# show ip route 10.0.0.6
% Subnet not in table
HQ-Router# show ip interface brief GigabitEthernet0/0
Interface                  IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0         10.0.0.1        YES manual up                    up""",
        "expected_fault": "Static route for 192.168.50.0/24 specifies non-existent next-hop 10.0.0.6 instead of valid next-hop 10.0.0.2",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "ROUTING",
        "severity": "High",
        "suggested_fix": """HQ-Router(config)# no ip route 192.168.50.0 255.255.255.0 10.0.0.6
HQ-Router(config)# ip route 192.168.50.0 255.255.255.0 10.0.0.2
HQ-Router(config)# end"""
    },
    {
        "case_id": "CASE-20",
        "title": "Inbound ACL Blocking Web Traffic to Server",
        "symptom": "External users cannot browse HTTP web server at 192.168.1.100; ICMP ping works.",
        "topology_note": "Router-1 Gi0/1 connects to Internet. Gi0/0 connects to DMZ (192.168.1.0/24).",
        "show_outputs": """Router-1# show access-lists 101
Extended IP access list 101
    10 permit icmp any any (45 matches)
    20 deny tcp any host 192.168.1.100 eq www (128 matches)
    30 permit ip any any
Router-1# show ip interface GigabitEthernet0/1 | include Inbound
  Inbound access list is 101""",
        "expected_fault": "Extended ACL 101 line 20 explicitly denies TCP port 80 (HTTP) to web server 192.168.1.100",
        "osi_layer": "Layer 4 - Transport",
        "concept_tag": "ACL",
        "severity": "High",
        "suggested_fix": """Router-1(config)# ip access-list extended 101
Router-1(config-ext-nacl)# no 20
Router-1(config-ext-nacl)# 20 permit tcp any host 192.168.1.100 eq 80
Router-1(config-ext-nacl)# end"""
    },
    {
        "case_id": "CASE-21",
        "title": "Implicit Deny All Blocking Inter-VLAN Traffic",
        "symptom": "VLAN 10 clients cannot ping or communicate with VLAN 20 database server 192.168.20.50.",
        "topology_note": "Router-1 sub-interface Gi0/0.10 has inbound ACL applied.",
        "show_outputs": """Router-1# show run interface GigabitEthernet0/0.10
interface GigabitEthernet0/0.10
 encapsulation dot1Q 10
 ip address 192.168.10.1 255.255.255.0
 ip access-group FILTER_MGMT in
Router-1# show access-lists FILTER_MGMT
Standard IP access list FILTER_MGMT
    10 permit 192.168.10.10 (only admin PC)
    (implicit deny any matches: 412)""",
        "expected_fault": "Standard ACL FILTER_MGMT only permits admin IP 192.168.10.10 and hits implicit deny all for all other VLAN 10 hosts",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "ACL",
        "severity": "High",
        "suggested_fix": """Router-1(config)# ip access-list standard FILTER_MGMT
Router-1(config-std-nacl)# 20 permit 192.168.10.0 0.0.0.255
Router-1(config-std-nacl)# end"""
    },
    {
        "case_id": "CASE-22",
        "title": "ACL Applied in Wrong Direction on Router Interface",
        "symptom": "All outbound traffic from internal LAN 10.1.1.0/24 is blocked at Router-1.",
        "topology_note": "LAN connected to Router-1 Gi0/0. ACL 105 intended to filter incoming traffic from Internet.",
        "show_outputs": """Router-1# show ip interface GigabitEthernet0/0
GigabitEthernet0/0 is up, line protocol is up
  Inbound access list is not set
  Outbound access list is 105
Router-1# show access-lists 105
Extended IP access list 105
    10 permit tcp host 203.0.113.50 any eq www
    20 deny ip any any (530 matches)""",
        "expected_fault": "ACL 105 was mistakenly applied as 'outbound' on LAN interface Gi0/0 instead of 'inbound' on WAN interface",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "ACL",
        "severity": "Critical",
        "suggested_fix": """Router-1(config)# interface GigabitEthernet0/0
Router-1(config-if)# no ip access-group 105 out
Router-1(config-if)# interface GigabitEthernet0/1
Router-1(config-if)# ip access-group 105 in
Router-1(config-if)# end"""
    },
    {
        "case_id": "CASE-23",
        "title": "NAT Inside/Outside Interface Designations Inverted",
        "symptom": "Internal hosts cannot access Internet; NAT translations table is completely empty.",
        "topology_note": "Router-1 connects to LAN (Gi0/0) and WAN/ISP (Gi0/1). NAT Overload configured.",
        "show_outputs": """Router-1# show ip nat translations
(Empty)
Router-1# show run interface GigabitEthernet0/0
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 ip nat outside
Router-1# show run interface GigabitEthernet0/1
interface GigabitEthernet0/1
 ip address 203.0.113.2 255.255.255.252
 ip nat inside""",
        "expected_fault": "NAT inside and outside designations are reversed: LAN Gi0/0 is set to 'outside' and WAN Gi0/1 is set to 'inside'",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "NAT",
        "severity": "Critical",
        "suggested_fix": """Router-1(config)# interface GigabitEthernet0/0
Router-1(config-if)# no ip nat outside
Router-1(config-if)# ip nat inside
Router-1(config-if)# interface GigabitEthernet0/1
Router-1(config-if)# no ip nat inside
Router-1(config-if)# ip nat outside
Router-1(config-if)# end"""
    },
    {
        "case_id": "CASE-24",
        "title": "NAT ACL Missing Subnet in Permitted Source List",
        "symptom": "Hosts in new subnet 192.168.20.0/24 cannot access Internet while 192.168.10.0/24 hosts can.",
        "topology_note": "Router-1 has NAT Overload configured referencing standard ACL 1.",
        "show_outputs": """Router-1# show run | include ip nat inside source
ip nat inside source list 1 interface GigabitEthernet0/1 overload
Router-1# show access-lists 1
Standard IP access list 1
    10 permit 192.168.10.0, wildcard bits 0.0.0.255 (234 matches)
Router-1# show ip nat statistics
Total active translations: 12 (0 static, 12 dynamic; 12 extended)
Outside interfaces: GigabitEthernet0/1
Inside interfaces: GigabitEthernet0/0.10, GigabitEthernet0/0.20""",
        "expected_fault": "Standard ACL 1 referenced by NAT overload does not include permit statement for VLAN 20 subnet 192.168.20.0/24",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "NAT",
        "severity": "High",
        "suggested_fix": """Router-1(config)# access-list 1 permit 192.168.20.0 0.0.0.255
Router-1(config)# end"""
    },
    {
        "case_id": "CASE-25",
        "title": "NAT Overload Missing 'overload' Keyword",
        "symptom": "Only the first internal PC can access Internet; all subsequent PCs get timed-out connection.",
        "topology_note": "Router-1 has single public IP on WAN interface Gi0/1 (203.0.113.2).",
        "show_outputs": """Router-1# show run | include ip nat inside source
ip nat inside source list 10 interface GigabitEthernet0/1
Router-1# show ip nat translations
Pro Inside global      Inside local       Outside local      Outside global
--- 203.0.113.2        192.168.1.10       ---                ---
Router-1# show ip nat statistics
Hits: 50 Misses: 45
Expired translations: 0
Dynamic mappings:
-- Inside Source
access-list 10 interface GigabitEthernet0/1 ref count 1""",
        "expected_fault": "NAT statement lacks the 'overload' (PAT) keyword, exhausting the single public IP after one host translation",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "NAT",
        "severity": "Critical",
        "suggested_fix": """Router-1(config)# no ip nat inside source list 10 interface GigabitEthernet0/1
Router-1(config)# ip nat inside source list 10 interface GigabitEthernet0/1 overload
Router-1(config)# end"""
    },
    {
        "case_id": "CASE-26",
        "title": "Guest Wi-Fi Can Reach Internal Corporate Servers",
        "symptom": "Guest Wi-Fi laptops on SSID 'Corp-Guest' can ping internal accounting database server 10.10.50.10.",
        "topology_note": "WLC-1 / AP-1 provides 'Corp-Guest' (VLAN 40) and 'Corp-Internal' (VLAN 10). Router-1 handles inter-VLAN routing.",
        "show_outputs": """Guest-Laptop> ping 10.10.50.10
Reply from 10.10.50.10: bytes=32 time=2ms TTL=127
Router-1# show run interface GigabitEthernet0/0.40
interface GigabitEthernet0/0.40
 encapsulation dot1Q 40
 ip address 172.16.40.1 255.255.255.0
Router-1# show access-lists GUEST_ISOLATION
% No access list named GUEST_ISOLATION""",
        "expected_fault": "Guest Wi-Fi VLAN 40 lacks an inbound isolation ACL on Router-1 sub-interface Gi0/0.40",
        "osi_layer": "Layer 4 - Transport",
        "concept_tag": "WIRELESS",
        "severity": "High",
        "suggested_fix": """Router-1(config)# ip access-list extended GUEST_ISOLATION
Router-1(config-ext-nacl)# permit udp any any eq bootps
Router-1(config-ext-nacl)# permit udp any any eq domain
Router-1(config-ext-nacl)# deny ip 172.16.40.0 0.0.0.255 10.0.0.0 0.255.255.255
Router-1(config-ext-nacl)# permit ip 172.16.40.0 0.0.0.255 any
Router-1(config-ext-nacl)# interface GigabitEthernet0/0.40
Router-1(config-if)# ip access-group GUEST_ISOLATION in
Router-1(config-if)# end"""
    },
    {
        "case_id": "CASE-27",
        "title": "Port Security Err-Disabled on Access Switchport",
        "symptom": "User plugged personal laptop into desk port Fa0/8; port immediately went amber and disconnected.",
        "topology_note": "Switch-1 has port security enabled with maximum 1 MAC address on Fa0/8.",
        "show_outputs": """Switch-1# show interfaces FastEthernet0/8 status
Port      Name               Status       Vlan       Duplex  Speed Type
Fa0/8     Office-Desk-8      err-disabled 10           auto   auto 10/100BaseTX
Switch-1# show port-security interface FastEthernet0/8
Port Security              : Enabled
Port Status                : Secure-shutdown
Violation Mode             : Shutdown
Aging Time                 : 0 mins
Aging Type                 : Absolute
SecureStatic Address Aging : Disabled
Maximum MAC Addresses      : 1
Total MAC Addresses        : 1
Configured MAC Addresses   : 1
Sticky MAC Addresses       : 0
Last Source Address:Vlan   : 0004.9a12.88bb:10
Security Violation Count   : 1""",
        "expected_fault": "Port security violation triggered on Fa0/8 due to unauthorized MAC address, placing interface into err-disabled state",
        "osi_layer": "Layer 2 - Data Link",
        "concept_tag": "SECURITY",
        "severity": "Medium",
        "suggested_fix": """Switch-1(config)# interface FastEthernet0/8
Switch-1(config-if)# shutdown
Switch-1(config-if)# no switchport port-security mac-address 0001.4211.aacc
Switch-1(config-if)# switchport port-security mac-address sticky
Switch-1(config-if)# no shutdown
Switch-1(config-if)# end"""
    },
    {
        "case_id": "CASE-28",
        "title": "Duplex Mismatch Causing Packet Loss and Collision",
        "symptom": "Server transfers over Switch-1 Fa0/24 are extremely slow with 35% packet loss on large files.",
        "topology_note": "Switch-1 Fa0/24 connects to Linux Web Server. Switch port set to Half Duplex; Server NIC set to Full Duplex.",
        "show_outputs": """Switch-1# show interfaces FastEthernet0/24
FastEthernet0/24 is up, line protocol is up (connected)
  Hardware is Fast Ethernet, address is 0010.1122.3344
  Half-duplex, 100Mb/s, media type is 100BaseTX
  582914 input errors, 42180 CRC, 0 frame, 192045 runts
  389211 late collision, 94812 deferred, 1204 output buffer failures""",
        "expected_fault": "Duplex mismatch: Switch-1 Fa0/24 is manually forced to Half-duplex while Server NIC is Full-duplex causing collisions",
        "osi_layer": "Layer 1 - Physical",
        "concept_tag": "SWITCHING",
        "severity": "Medium",
        "suggested_fix": """Switch-1(config)# interface FastEthernet0/24
Switch-1(config-if)# duplex full
Switch-1(config-if)# speed 100
Switch-1(config-if)# end"""
    },
    {
        "case_id": "CASE-29",
        "title": "Switchport Administratively Shutdown",
        "symptom": "PC-5 is plugged into Switch-1 Fa0/10 with link LED completely dark and no network connectivity.",
        "topology_note": "PC-5 connected via straight-through Ethernet patch cable to Switch-1 Fa0/10.",
        "show_outputs": """Switch-1# show interfaces FastEthernet0/10
FastEthernet0/10 is administratively down, line protocol is down (disabled)
  Hardware is Fast Ethernet, address is 0001.9688.0010
  MTU 1500 bytes, BW 100000 Kbit/sec, DLY 100 usec
Switch-1# show ip interface brief FastEthernet0/10
Interface                  IP-Address      OK? Method Status                Protocol
FastEthernet0/10           unassigned      YES unset  administratively down down""",
        "expected_fault": "Port FastEthernet0/10 is administratively disabled (shutdown) in switch configuration",
        "osi_layer": "Layer 1 - Physical",
        "concept_tag": "SWITCHING",
        "severity": "Low",
        "suggested_fix": """Switch-1(config)# interface FastEthernet0/10
Switch-1(config-if)# no shutdown
Switch-1(config-if)# end"""
    },
    {
        "case_id": "CASE-30",
        "title": "Wireless AP SSID Mapped to Non-Existent VLAN",
        "symptom": "Wireless mobile devices associate to SSID 'Staff-Wlan' but cannot obtain IP or reach network.",
        "topology_note": "Cisco Lightweight WLC-2504 manages AP-1. SSID 'Staff-Wlan' interface is mapped to VLAN 55.",
        "show_outputs": """WLC-1# show wlan 1
WLAN Identifier.................................. 1
Profile Name..................................... Staff-Wlan
Network Name (SSID).............................. Staff-Wlan
Status........................................... Enabled
Interface........................................ staff-interface (VLAN 55)
Switch-Core# show vlan id 55
% VLAN 55 not found in current VLAN database""",
        "expected_fault": "SSID interface is mapped to VLAN 55 which does not exist on the upstream Core Switch",
        "osi_layer": "Layer 2 - Data Link",
        "concept_tag": "WIRELESS",
        "severity": "High",
        "suggested_fix": """Switch-Core(config)# vlan 55
Switch-Core(config-vlan)# name Staff-Wireless
Switch-Core(config-vlan)# end"""
    },
    {
        "case_id": "CASE-31",
        "title": "RIP Version 1 vs Version 2 Subnet Discard",
        "symptom": "Router-A (RIP v2) advertises subnets /28 but Router-B (RIP v1) discards classless updates.",
        "topology_note": "Router-A connects to Router-B over 10.1.1.0/30. Subnets are 172.16.1.16/28 and 172.16.1.32/28.",
        "show_outputs": """Router-A# show run | section router rip
router rip
 version 2
 network 10.0.0.0
 network 172.16.0.0
Router-B# show run | section router rip
router rip
 network 10.0.0.0
Router-B# show ip protocols | include Sending
  Sending updates every 30 seconds
  Invalid after 180 seconds, hold down 180, flushed after 240
  Outgoing update filter list for all interfaces is not set
  Incoming update filter list for all interfaces is not set
  Default version control: send version 1, receive version 1""",
        "expected_fault": "Router-B is running RIP version 1 (classful) which ignores classless subnet mask updates from Router-A",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "ROUTING",
        "severity": "Medium",
        "suggested_fix": """Router-B(config)# router rip
Router-B(config-router)# version 2
Router-B(config-router)# no auto-summary
Router-B(config-router)# end"""
    },
    {
        "case_id": "CASE-32",
        "title": "HSRP Virtual IP Mismatch with Client Default Gateway",
        "symptom": "When Router-1 (HSRP Active) fails, backup Router-2 takes over but clients lose connectivity.",
        "topology_note": "HSRP Group 1 on LAN 192.168.1.0/24. R1 is .2, R2 is .3, Virtual IP configured as 192.168.1.254.",
        "show_outputs": """PC-1> ipconfig
Default Gateway.................: 192.168.1.1
Router-1# show standby brief
                     P Active          Standby         Virtual IP
Gi0/0          1   P local           192.168.1.3     192.168.1.254
Router-2# show standby brief
                     P Active          Standby         Virtual IP
Gi0/0          1   P 192.168.1.2     local           192.168.1.254""",
        "expected_fault": "Clients are configured with static default gateway 192.168.1.1 instead of HSRP Virtual IP 192.168.1.254",
        "osi_layer": "Layer 3 - Network",
        "concept_tag": "GATEWAY",
        "severity": "High",
        "suggested_fix": "PC-1> ipconfig 192.168.1.50 255.255.255.0 192.168.1.254"
    }
]

out_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(out_dir, "cases.csv")

fieldnames = ["case_id", "title", "symptom", "topology_note", "show_outputs", "expected_fault", "osi_layer", "concept_tag", "severity", "suggested_fix"]

with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for case in cases_data:
        writer.writerow(case)

print(f"Successfully generated {len(cases_data)} cases in {csv_path}")
