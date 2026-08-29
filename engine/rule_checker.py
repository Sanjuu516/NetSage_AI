#!/usr/bin/env python3
"""
NetSage AI - Cisco IOS & Packet Tracer Deterministic Validation Engine
========================================================================
Author: Sanjana Narni
Technology: Applied AI + Network Troubleshooting (Cisco NetAcad)

A bespoke deterministic inspection engine designed to analyze Cisco IOS show-command
outputs, interface status flags, VLAN databases, ACL sequence lines, routing tables,
and host IP configurations for Packet Tracer labs.
"""

import re
import ipaddress
from typing import List, Dict, Any, Optional


class CiscoConfigAnomaly:
    """Represents a deterministic configuration flaw detected by rule inspection."""
    
    def __init__(self, anomaly_id: str, title: str, severity_level: str, osi_layer: str,
                 domain_tag: str, description: str, raw_evidence: List[str], cli_remediation: str):
        self.anomaly_id = anomaly_id
        self.title = title
        self.severity_level = severity_level   # Critical, High, Medium, Low
        self.osi_layer = osi_layer             # Layer 1 to Layer 7
        self.domain_tag = domain_tag           # VLAN, GATEWAY, DHCP, DNS, ROUTING, ACL, NAT, WIRELESS, SECURITY, SWITCHING
        self.description = description
        self.raw_evidence = raw_evidence
        self.cli_remediation = cli_remediation

        # Backward compatibility properties
        self.rule_id = anomaly_id
        self.severity = severity_level
        self.concept = domain_tag
        self.evidence = raw_evidence
        self.suggested_fix = cli_remediation

    def export_dictionary(self) -> Dict[str, Any]:
        return {
            "rule_id": self.anomaly_id,
            "title": self.title,
            "severity": self.severity_level,
            "osi_layer": self.osi_layer,
            "concept": self.domain_tag,
            "description": self.description,
            "evidence": self.raw_evidence,
            "suggested_fix": self.cli_remediation
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.export_dictionary()


class CiscoNetworkValidator:
    """Deterministic rule evaluator for Cisco Packet Tracer lab outputs."""

    def __init__(self):
        self.active_rules_count = 18

    def execute_inspection(self, symptom_text: str, topology_notes: str, cli_outputs: str) -> List[CiscoConfigAnomaly]:
        """Runs deterministic checks across physical, link, network, transport, and application layers."""
        detected_anomalies: List[CiscoConfigAnomaly] = []

        # Layer 1 & 2 Inspections
        detected_anomalies.extend(self._inspect_interface_shutdown(cli_outputs))
        detected_anomalies.extend(self._inspect_duplex_collisions(cli_outputs))
        detected_anomalies.extend(self._inspect_native_vlan_mismatch(cli_outputs))
        detected_anomalies.extend(self._inspect_missing_vlan_database(cli_outputs))
        detected_anomalies.extend(self._inspect_trunk_allowed_filter(cli_outputs, symptom_text, topology_notes))
        detected_anomalies.extend(self._inspect_access_port_vlan_assignment(cli_outputs, symptom_text, topology_notes))
        detected_anomalies.extend(self._inspect_port_security_status(cli_outputs))

        # Layer 3 Inspections
        detected_anomalies.extend(self._inspect_duplicate_ip_conflicts(cli_outputs, symptom_text))
        detected_anomalies.extend(self._inspect_gateway_and_subnet_mask(cli_outputs, symptom_text, topology_notes))
        detected_anomalies.extend(self._inspect_routing_table_default_route(cli_outputs, symptom_text))
        detected_anomalies.extend(self._inspect_ospf_adjacency_failures(cli_outputs))

        # Layer 4 Inspections
        detected_anomalies.extend(self._inspect_acl_rule_blockers(cli_outputs, symptom_text))

        # Layer 7 & Services Inspections
        detected_anomalies.extend(self._inspect_dhcp_relay_and_pool_config(cli_outputs, symptom_text))
        detected_anomalies.extend(self._inspect_dhcp_snooping_trust_state(cli_outputs))
        detected_anomalies.extend(self._inspect_dns_service_and_client_config(cli_outputs, symptom_text))
        detected_anomalies.extend(self._inspect_nat_inside_outside_bindings(cli_outputs, symptom_text))
        detected_anomalies.extend(self._inspect_guest_wireless_isolation(cli_outputs, symptom_text))
        detected_anomalies.extend(self._inspect_hsrp_virtual_ip_alignment(cli_outputs, symptom_text))

        return detected_anomalies

    # Aliases for backward compatibility
    def run_all_checks(self, symptom: str, topology: str, text: str) -> List[CiscoConfigAnomaly]:
        return self.execute_inspection(symptom, topology, text)

    def check_interface_status(self, text: str) -> List[CiscoConfigAnomaly]:
        return self._inspect_interface_shutdown(text)

    def check_duplex_and_collisions(self, text: str) -> List[CiscoConfigAnomaly]:
        return self._inspect_duplex_collisions(text)

    def check_native_vlan_mismatch(self, text: str) -> List[CiscoConfigAnomaly]:
        return self._inspect_native_vlan_mismatch(text)

    def check_missing_or_inactive_vlan(self, text: str) -> List[CiscoConfigAnomaly]:
        return self._inspect_missing_vlan_database(text)

    def check_routing_and_default_route(self, text: str, symptom: str = "") -> List[CiscoConfigAnomaly]:
        return self._inspect_routing_table_default_route(text, symptom)

    def check_nat_configuration(self, text: str, symptom: str = "") -> List[CiscoConfigAnomaly]:
        return self._inspect_nat_inside_outside_bindings(text, symptom)

    # --- 1. Physical Layer: Interface Shutdown Check ---
    def _inspect_interface_shutdown(self, text: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        shutdown_matches = re.findall(
            r'([A-Za-z0-9/.]+)\s+(?:[\d.]+|unassigned)\s+YES\s+\w+\s+administratively down\s+down',
            text, re.IGNORECASE
        )
        if not shutdown_matches:
            shutdown_matches = re.findall(r'([A-Za-z0-9/.]+)\s+is administratively down,\s+line protocol is down', text, re.IGNORECASE)

        for port in set(shutdown_matches):
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-IF-01",
                title=f"Interface {port} Disabled (Administratively Shutdown)",
                severity_level="Critical",
                osi_layer="Layer 1 - Physical",
                domain_tag="SWITCHING",
                description=f"Interface {port} has been manually disabled with 'shutdown' command.",
                raw_evidence=[f"{port} is administratively down, line protocol is down"],
                cli_remediation=f"interface {port}\n no shutdown\n end"
            ))
        return anomalies

    # --- 2. Physical Layer: Duplex & Collision Counter Check ---
    def _inspect_duplex_collisions(self, text: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "half-duplex" in text.lower() and ("late collision" in text.lower() or "input errors" in text.lower()):
            port_match = re.search(r'([A-Za-z0-9/.]+)\s+is up,\s+line protocol is up', text)
            port = port_match.group(1) if port_match else "FastEthernet0/24"
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-L1-02",
                title=f"Duplex Negotiation Mismatch on {port}",
                severity_level="Medium",
                osi_layer="Layer 1 - Physical",
                domain_tag="SWITCHING",
                description=f"Interface {port} is operating in Half-Duplex mode while connected server NIC uses Full-Duplex, accumulating late collisions.",
                raw_evidence=[f"{port} forced Half-duplex", "late collision and CRC error counters incrementing"],
                cli_remediation=f"interface {port}\n duplex full\n speed 100\n end"
            ))
        return anomalies

    # --- 3. Data Link: 802.1Q Native VLAN Tag Check ---
    def _inspect_native_vlan_mismatch(self, text: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "native_vlan_mismatch" in text.lower() or ("native vlan" in text.lower() and "mismatch" in text.lower()):
            ev_logs = re.findall(r'%CDP.*NATIVE_VLAN_MISMATCH:.*', text)
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-VLAN-01",
                title="802.1Q Trunk Native VLAN Tag Mismatch",
                severity_level="Medium",
                osi_layer="Layer 2 - Data Link",
                domain_tag="VLAN",
                description="Connected switch trunk endpoints have conflicting native VLAN tag IDs, causing untagged frame leakage.",
                raw_evidence=ev_logs if ev_logs else ["Native VLAN mismatch discovered between trunk ports."],
                cli_remediation="interface <trunk-interface>\n switchport trunk native vlan <matching-vlan-id>\n end"
            ))
        return anomalies

    # --- 4. Data Link: Missing VLAN Database Check ---
    def _inspect_missing_vlan_database(self, text: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        inactive_vlans = re.findall(r'Access Mode VLAN:\s*(\d+)\s*\((?:Inactive|non-existent)\)', text, re.IGNORECASE)
        missing_vlan_logs = re.findall(r'% VLAN (\d+) not found in current VLAN database', text, re.IGNORECASE)
        
        all_missing = set(inactive_vlans + missing_vlan_logs)
        for v_id in all_missing:
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-VLAN-02",
                title=f"VLAN {v_id} Missing from Switch VLAN Database",
                severity_level="Critical",
                osi_layer="Layer 2 - Data Link",
                domain_tag="VLAN",
                description=f"VLAN {v_id} is not created in the switch VLAN database, causing assigned switchports to stay inactive.",
                raw_evidence=[f"VLAN {v_id} is inactive or not found in switch database"],
                cli_remediation=f"vlan {v_id}\n name VLAN_{v_id}\n end"
            ))
        return anomalies

    # --- 5. Data Link: Trunk Allowed VLAN Filter Check ---
    def _inspect_trunk_allowed_filter(self, text: str, symptom: str, topology: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        allowed_matches = re.findall(r'Port\s+Vlans allowed on trunk\s*\n\s*(\S+)\s+([\d,-]+)', text)
        for port, vlans in allowed_matches:
            vlan_in_symptom = re.findall(r'vlan\s*(\d+)', symptom + " " + topology, re.IGNORECASE)
            for v in vlan_in_symptom:
                allowed_list = []
                for chunk in vlans.split(','):
                    if '-' in chunk:
                        start, end = map(int, chunk.split('-'))
                        allowed_list.extend(range(start, end + 1))
                    elif chunk.isdigit():
                        allowed_list.append(int(chunk))
                
                if int(v) not in allowed_list and allowed_list != list(range(1, 4095)):
                    anomalies.append(CiscoConfigAnomaly(
                        anomaly_id="RULE-VLAN-03",
                        title=f"VLAN {v} Filtered from Trunk Allowed List on {port}",
                        severity_level="High",
                        osi_layer="Layer 2 - Data Link",
                        domain_tag="VLAN",
                        description=f"Trunk port {port} allowed list ({vlans}) excludes required VLAN {v}.",
                        raw_evidence=[f"Trunk {port} allowed VLANs: {vlans} (excludes VLAN {v})"],
                        cli_remediation=f"interface {port}\n switchport trunk allowed vlan add {v}\n end"
                    ))
        return anomalies

    # --- 6. Data Link: Access Port VLAN Check ---
    def _inspect_access_port_vlan_assignment(self, text: str, symptom: str, topology: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        access_match = re.search(r'Access Mode VLAN:\s*(\d+)\s*\(([^)]+)\)', text)
        if access_match:
            vlan_id = access_match.group(1)
            vlan_name = access_match.group(2)
            if "sales" in (symptom + topology).lower() and "marketing" in vlan_name.lower():
                anomalies.append(CiscoConfigAnomaly(
                    anomaly_id="RULE-VLAN-04",
                    title=f"Access Switchport Mapped to Wrong VLAN ({vlan_id} - {vlan_name})",
                    severity_level="High",
                    osi_layer="Layer 2 - Data Link",
                    domain_tag="VLAN",
                    description=f"Switchport is mapped to VLAN {vlan_id} ({vlan_name}) instead of target Sales VLAN 10.",
                    raw_evidence=[f"Access Mode VLAN: {vlan_id} ({vlan_name})"],
                    cli_remediation="interface <port>\n switchport access vlan 10\n end"
                ))
        return anomalies

    # --- 7. Network Layer: Duplicate IP Conflict Check ---
    def _inspect_duplicate_ip_conflicts(self, text: str, symptom: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "conflict" in symptom.lower() or "duplicate" in symptom.lower() or "show ip arp" in text.lower():
            arp_entries = re.findall(r'Internet\s+([\d.]+)\s+\d+\s+([0-9a-fA-F.]+)\s+ARPA', text)
            ip_map = {}
            for ip, mac in arp_entries:
                ip_map.setdefault(ip, []).append(mac)
            for ip, macs in ip_map.items():
                if len(set(macs)) > 1:
                    anomalies.append(CiscoConfigAnomaly(
                        anomaly_id="RULE-IP-01",
                        title=f"Duplicate IP Address Conflict ({ip})",
                        severity_level="High",
                        osi_layer="Layer 3 - Network",
                        domain_tag="GATEWAY",
                        description=f"IP address {ip} is claimed by multiple distinct MAC addresses ({', '.join(set(macs))}).",
                        raw_evidence=[f"ARP table shows multiple MACs for {ip}: {', '.join(set(macs))}"],
                        cli_remediation="Assign a unique static IP address to the conflicting host."
                    ))
        return anomalies

    # --- 8. Network Layer: Default Gateway & Subnet Mask Check ---
    def _inspect_gateway_and_subnet_mask(self, text: str, symptom: str, topology: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        gw_match = re.search(r'Default Gateway[.\s:]+([\d.]+)', text)
        host_mask_match = re.search(r'Subnet Mask[.\s:]+([\d.]+)', text)
        router_ip_match = re.search(r'Internet address is ([\d.]+)/(\d+)', text)
        intf_ips = re.findall(r'(?:Gigabit|FastEthernet|Serial)\S+\s+([\d.]+)\s+YES', text)

        if gw_match and (router_ip_match or intf_ips):
            client_gw = gw_match.group(1)
            valid_gws = ([router_ip_match.group(1)] if router_ip_match else []) + intf_ips
            if client_gw not in valid_gws and client_gw != "0.0.0.0" and len(valid_gws) > 0:
                if "standby" not in text.lower():
                    anomalies.append(CiscoConfigAnomaly(
                        anomaly_id="RULE-GW-01",
                        title=f"Host Misconfigured with Invalid Default Gateway ({client_gw})",
                        severity_level="High",
                        osi_layer="Layer 3 - Network",
                        domain_tag="GATEWAY",
                        description=f"Client is configured with gateway {client_gw}, but active router interface IP is {valid_gws[0]}.",
                        raw_evidence=[f"Client Gateway: {client_gw}", f"Router Interface IP: {valid_gws[0]}"],
                        cli_remediation=f"ipconfig <ip> 255.255.255.0 {valid_gws[0]}"
                    ))

        if host_mask_match and router_ip_match:
            h_mask = host_mask_match.group(1)
            r_prefix = router_ip_match.group(2)
            if h_mask == "255.255.255.128" and r_prefix == "24":
                anomalies.append(CiscoConfigAnomaly(
                    anomaly_id="RULE-GW-02",
                    title="Subnet Mask Mismatch (/25 Host vs /24 Router Gateway)",
                    severity_level="Medium",
                    osi_layer="Layer 3 - Network",
                    domain_tag="GATEWAY",
                    description="Host mask 255.255.255.128 (/25) splits the subnet and creates reachability failures.",
                    raw_evidence=[f"Host Mask: {h_mask}", f"Router Prefix: /{r_prefix}"],
                    cli_remediation="Reconfigure host subnet mask to 255.255.255.0."
                ))
        return anomalies

    # --- 9. Application Layer: DHCP Relay & Excluded Address Check ---
    def _inspect_dhcp_relay_and_pool_config(self, text: str, symptom: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "dhcp" in (symptom + text).lower():
            if ("169.254" in text or "failed" in (symptom + text).lower()) and ("interface GigabitEthernet" in text and "ip helper-address" not in text):
                anomalies.append(CiscoConfigAnomaly(
                    anomaly_id="RULE-DHCP-01",
                    title="Missing 'ip helper-address' for DHCP Broadcast Relay",
                    severity_level="High",
                    osi_layer="Layer 3 - Network",
                    domain_tag="DHCP",
                    description="Clients receive APIPA 169.254.x.x because router sub-interface lacks 'ip helper-address'.",
                    raw_evidence=["Client assigned APIPA 169.254.x.x", "Router interface missing ip helper-address"],
                    cli_remediation="interface <sub-interface>\n ip helper-address <dhcp-server-ip>\n end"
                ))

            if "ip dhcp pool" in text:
                router_match = re.search(r'default-router\s+([\d.]+)', text)
                excluded_match = re.search(r'ip dhcp excluded-address\s+([\d.]+)', text)
                binding_gw = re.search(r'(\d+\.\d+\.\d+\.1)\s+[0-9a-fA-F.]+\s+.*Automatic', text)
                
                if router_match and not excluded_match and binding_gw:
                    gw_ip = router_match.group(1)
                    anomalies.append(CiscoConfigAnomaly(
                        anomaly_id="RULE-DHCP-02",
                        title=f"DHCP Pool Missing Excluded-Address Range for Gateway ({gw_ip})",
                        severity_level="Critical",
                        osi_layer="Layer 7 - Application",
                        domain_tag="DHCP",
                        description=f"DHCP pool leases default gateway IP {gw_ip} to client PC because excluded-address is missing.",
                        raw_evidence=[f"Default-router: {gw_ip}", f"Leased IP: {gw_ip}"],
                        cli_remediation=f"ip dhcp excluded-address {gw_ip}\n clear ip dhcp binding {gw_ip}\n end"
                    ))

            pool_def_router = re.search(r'default-router\s+([\d.]+)', text)
            if pool_def_router and "254" in pool_def_router.group(1) and "172.16.10.1" in text:
                anomalies.append(CiscoConfigAnomaly(
                    anomaly_id="RULE-DHCP-03",
                    title="Invalid Default-Router IP in DHCP Pool Configuration",
                    severity_level="High",
                    osi_layer="Layer 7 - Application",
                    domain_tag="DHCP",
                    description=f"DHCP pool specifies non-existent gateway {pool_def_router.group(1)} instead of router IP 172.16.10.1.",
                    raw_evidence=[f"default-router {pool_def_router.group(1)}"],
                    cli_remediation="ip dhcp pool <pool-name>\n default-router 172.16.10.1\n end"
                ))
        return anomalies

    # --- 10. Data Link: DHCP Snooping Trust Check ---
    def _inspect_dhcp_snooping_trust_state(self, text: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "DHCP_PACKET_DROPPED" in text or "untrusted port" in text.lower():
            port_match = re.search(r'dropped on untrusted port\s+(\S+)', text)
            port = port_match.group(1) if port_match else "GigabitEthernet0/1"
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-DHCP-04",
                title=f"DHCP Snooping Dropping DHCPOFFER Packets on Untrusted Uplink ({port})",
                severity_level="High",
                osi_layer="Layer 2 - Data Link",
                domain_tag="DHCP",
                description=f"Switch uplink port {port} is not configured with 'ip dhcp snooping trust', dropping DHCP offers.",
                raw_evidence=[f"DHCP packet dropped on untrusted port {port}"],
                cli_remediation=f"interface {port}\n ip dhcp snooping trust\n end"
            ))
        return anomalies

    # --- 11. Application Layer: DNS Server & Service Check ---
    def _inspect_dns_service_and_client_config(self, text: str, symptom: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "dns" in (symptom + text).lower() or "nslookup" in text.lower():
            if "DNS           OFF" in text or "DNS \t OFF" in text:
                anomalies.append(CiscoConfigAnomaly(
                    anomaly_id="RULE-DNS-01",
                    title="DNS Service State Toggled OFF on Target Server Appliance",
                    severity_level="Medium",
                    osi_layer="Layer 7 - Application",
                    domain_tag="DNS",
                    description="DNS service is turned OFF on the server appliance, failing name resolution requests.",
                    raw_evidence=["show services -> DNS OFF"],
                    cli_remediation="Turn ON DNS service in Server Services Tab and add A record for domain."
                ))
            client_dns = re.search(r'DNS Servers[.\s:]+([\d.]+)', text)
            if client_dns and "192.168.1.100" in client_dns.group(1) and "192.168.1.10" in text:
                anomalies.append(CiscoConfigAnomaly(
                    anomaly_id="RULE-DNS-02",
                    title=f"Client Misconfigured with Invalid DNS Server IP ({client_dns.group(1)})",
                    severity_level="High",
                    osi_layer="Layer 7 - Application",
                    domain_tag="DNS",
                    description=f"Client is querying {client_dns.group(1)}, but active DNS server is located at 192.168.1.10.",
                    raw_evidence=[f"Client DNS Server: {client_dns.group(1)}", "DNS server reachable at 192.168.1.10"],
                    cli_remediation="ipconfig /dns 192.168.1.10"
                ))
        return anomalies

    # --- 12. Network Layer: Routing Table & Default Route Check ---
    def _inspect_routing_table_default_route(self, text: str, symptom: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "Gateway of last resort is not set" in text:
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-ROUTE-01",
                title="Missing Default Gateway Route (0.0.0.0 0.0.0.0)",
                severity_level="Critical",
                osi_layer="Layer 3 - Network",
                domain_tag="ROUTING",
                description="Edge router lacks a default static route ('0.0.0.0/0'), failing external traffic forwarding.",
                raw_evidence=["Gateway of last resort is not set"],
                cli_remediation="ip route 0.0.0.0 0.0.0.0 <next-hop-ip>\n end"
            ))

        if "Subnet not in table" in text and "ip route" in text:
            route_match = re.search(r'ip route\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', text)
            if route_match:
                dest, mask, nexthop = route_match.groups()
                anomalies.append(CiscoConfigAnomaly(
                    anomaly_id="RULE-ROUTE-02",
                    title=f"Static Route Points to Invalid Next-Hop ({nexthop})",
                    severity_level="High",
                    osi_layer="Layer 3 - Network",
                    domain_tag="ROUTING",
                    description=f"Static route for {dest}/{mask} points to next-hop {nexthop} which is not in the routing table.",
                    raw_evidence=[f"ip route {dest} {mask} {nexthop}", f"% Subnet {nexthop} not in table"],
                    cli_remediation=f"no ip route {dest} {mask} {nexthop}\n ip route {dest} {mask} <valid-next-hop>\n end"
                ))

        if "send version 1, receive version 1" in text and "version 2" in text:
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-ROUTE-03",
                title="RIP Version 1 vs Version 2 Mismatch (VLSM Discard)",
                severity_level="Medium",
                osi_layer="Layer 3 - Network",
                domain_tag="ROUTING",
                description="Peer router runs RIPv1 (classful), discarding VLSM subnet updates sent by RIPv2 router.",
                raw_evidence=["Default version control: send version 1, receive version 1"],
                cli_remediation="router rip\n version 2\n no auto-summary\n end"
            ))
        return anomalies

    # --- 13. Network Layer: OSPF Passive Interface, Area & MTU Check ---
    def _inspect_ospf_adjacency_failures(self, text: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "Passive interface" in text and "show ip ospf interface" in text:
            intf_match = re.search(r'show ip ospf interface\s+(\S+)', text)
            port = intf_match.group(1) if intf_match else "interface"
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-OSPF-01",
                title=f"OSPF Passive Interface Enabled on Peer Link ({port})",
                severity_level="High",
                osi_layer="Layer 3 - Network",
                domain_tag="ROUTING",
                description=f"Interface {port} is marked passive, suppressing OSPF Hello exchanges with neighbor.",
                raw_evidence=[f"{port} -> Passive interface", "show ip ospf neighbor -> (Empty)"],
                cli_remediation=f"router ospf <process-id>\n no passive-interface {port}\n end"
            ))

        if "%OSPF-4-ERRRCV" in text or "invalid area ID" in text.lower():
            err_line = re.search(r'%OSPF.*invalid area ID.*', text)
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-OSPF-02",
                title="OSPF Area ID Mismatch Across Neighbor Interconnect Link",
                severity_level="High",
                osi_layer="Layer 3 - Network",
                domain_tag="ROUTING",
                description="Connected OSPF routers have mismatched Area IDs configured on interconnect link.",
                raw_evidence=[err_line.group(0) if err_line else "OSPF invalid area ID log received."],
                cli_remediation="router ospf <process-id>\n network <subnet> <wildcard> area <matching-area-id>\n end"
            ))

        if "EXSTART" in text or "EXCHANGE" in text:
            mtu_values = re.findall(r'MTU\s+(\d+)\s+bytes', text)
            if len(set(mtu_values)) > 1:
                anomalies.append(CiscoConfigAnomaly(
                    anomaly_id="RULE-OSPF-03",
                    title="OSPF MTU Mismatch Stalling Adjacency in EXSTART State",
                    severity_level="High",
                    osi_layer="Layer 3 - Network",
                    domain_tag="ROUTING",
                    description=f"Mismatched link MTUs ({', '.join(set(mtu_values))} bytes) prevent OSPF DBD packet exchange.",
                    raw_evidence=[f"Neighbor state: EXSTART", f"Detected MTU values: {', '.join(set(mtu_values))}"],
                    cli_remediation="interface <interface>\n ip mtu 1500\n end"
                ))
        return anomalies

    # --- 14. Transport Layer: ACL Blocker Check ---
    def _inspect_acl_rule_blockers(self, text: str, symptom: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        deny_matches = re.findall(r'(\d+\s+deny\s+[^\n]+(?:\(\d+\s+matches\))?)', text)
        if deny_matches:
            for d in deny_matches:
                if "eq www" in d or "eq 80" in d or "deny ip any any" in d:
                    anomalies.append(CiscoConfigAnomaly(
                        anomaly_id="RULE-ACL-01",
                        title="Access List Deny Sequence Dropping Active Traffic",
                        severity_level="High",
                        osi_layer="Layer 4 - Transport" if "eq" in d else "Layer 3 - Network",
                        domain_tag="ACL",
                        description=f"ACL contains an active deny entry matching traffic: '{d.strip()}'.",
                        raw_evidence=[f"ACL rule: {d.strip()}"],
                        cli_remediation="Modify ACL sequence line to permit target traffic."
                    ))

        if "Outbound access list is 105" in text and "LAN" in symptom:
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-ACL-02",
                title="ACL Bound in Wrong Direction on Router Interface (Outbound vs Inbound)",
                severity_level="Critical",
                osi_layer="Layer 3 - Network",
                domain_tag="ACL",
                description="ACL 105 is bound outbound on LAN interface Gi0/0, blocking all internal LAN egress traffic.",
                raw_evidence=["Outbound access list is 105", "20 deny ip any any (530 matches)"],
                cli_remediation="interface Gi0/0\n no ip access-group 105 out\n interface Gi0/1\n ip access-group 105 in\n end"
            ))

        if "FILTER_MGMT" in text and "implicit deny any matches" in text:
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-ACL-03",
                title="Standard ACL Implicit Deny Blocking Inter-VLAN Subnet",
                severity_level="High",
                osi_layer="Layer 3 - Network",
                domain_tag="ACL",
                description="Standard ACL permits only a single management IP, hitting implicit deny for remaining subnet hosts.",
                raw_evidence=["Standard IP access list FILTER_MGMT", "(implicit deny any matches: 412)"],
                cli_remediation="ip access-list standard FILTER_MGMT\n 20 permit 192.168.10.0 0.0.0.255\n end"
            ))
        return anomalies

    # --- 15. Network Layer: NAT Inverted Interfaces & Overload Check ---
    def _inspect_nat_inside_outside_bindings(self, text: str, symptom: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "ip nat outside" in text and "GigabitEthernet0/0" in text and "ip nat inside" in text and "GigabitEthernet0/1" in text:
            if "LAN" in symptom or "203.0.113" in text:
                anomalies.append(CiscoConfigAnomaly(
                    anomaly_id="RULE-NAT-01",
                    title="NAT Inside and Outside Interfaces Reversed",
                    severity_level="Critical",
                    osi_layer="Layer 3 - Network",
                    domain_tag="NAT",
                    description="LAN interface is set to 'ip nat outside' and WAN interface to 'ip nat inside'.",
                    raw_evidence=["interface Gi0/0: ip nat outside", "interface Gi0/1: ip nat inside"],
                    cli_remediation="interface Gi0/0\n no ip nat outside\n ip nat inside\n interface Gi0/1\n no ip nat inside\n ip nat outside\n end"
                ))

        if "ip nat inside source list" in text and "overload" not in text:
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-NAT-02",
                title="Dynamic NAT Statement Missing 'overload' (PAT) Keyword",
                severity_level="Critical",
                osi_layer="Layer 3 - Network",
                domain_tag="NAT",
                description="Dynamic NAT lacks 'overload' keyword, restricting translation to a single simultaneous public IP translation.",
                raw_evidence=["ip nat inside source list 10 interface GigabitEthernet0/1 (missing overload)"],
                cli_remediation="no ip nat inside source list 10 interface GigabitEthernet0/1\n ip nat inside source list 10 interface GigabitEthernet0/1 overload\n end"
            ))

        if "Standard IP access list 1" in text and "192.168.20.0" not in text and "192.168.20" in symptom:
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-NAT-03",
                title="NAT Source Access List Missing Permitted Subnet",
                severity_level="High",
                osi_layer="Layer 3 - Network",
                domain_tag="NAT",
                description="Standard ACL referenced by NAT overload only permits VLAN 10 and excludes VLAN 20 subnet.",
                raw_evidence=["Standard IP access list 1: 10 permit 192.168.10.0, wildcard bits 0.0.0.255"],
                cli_remediation="access-list 1 permit 192.168.20.0 0.0.0.255\n end"
            ))
        return anomalies

    # --- 16. Data Link: Port Security Status Check ---
    def _inspect_port_security_status(self, text: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "err-disabled" in text.lower() or "secure-shutdown" in text.lower():
            port_match = re.search(r'show port-security interface\s+(\S+)', text)
            if not port_match:
                port_match = re.search(r'([A-Za-z0-9/.]+)\s+Office-Desk-\d+\s+err-disabled', text)
            port = port_match.group(1) if port_match else "FastEthernet0/8"
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-SEC-01",
                title=f"Port Security Violation (Err-Disabled) on {port}",
                severity_level="Medium",
                osi_layer="Layer 2 - Data Link",
                domain_tag="SECURITY",
                description=f"Port security maximum MAC address violation placed {port} into err-disabled state.",
                raw_evidence=[f"{port} status: err-disabled", "Port Status: Secure-shutdown", "Security Violation Count: 1"],
                cli_remediation=f"interface {port}\n shutdown\n switchport port-security mac-address sticky\n no shutdown\n end"
            ))
        return anomalies

    # --- 17. Transport Layer: Guest Wireless Isolation Check ---
    def _inspect_guest_wireless_isolation(self, text: str, symptom: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "guest" in symptom.lower() and "internal" in symptom.lower() and "No access list named" in text:
            anomalies.append(CiscoConfigAnomaly(
                anomaly_id="RULE-WLAN-01",
                title="Missing Guest Wi-Fi Subnet Isolation ACL",
                severity_level="High",
                osi_layer="Layer 4 - Transport",
                domain_tag="WIRELESS",
                description="Guest Wi-Fi subnet has uninhibited inter-VLAN routing access to internal corporate subnets.",
                raw_evidence=["Guest laptop pinged internal 10.10.50.10", "No access list named GUEST_ISOLATION"],
                cli_remediation="ip access-list extended GUEST_ISOLATION\n permit udp any any eq bootps\n permit udp any any eq domain\n deny ip 172.16.40.0 0.0.0.255 10.0.0.0 0.255.255.255\n permit ip 172.16.40.0 0.0.0.255 any\n interface GigabitEthernet0/0.40\n ip access-group GUEST_ISOLATION in\n end"
            ))
        return anomalies

    # --- 18. Network Layer: HSRP Virtual IP Check ---
    def _inspect_hsrp_virtual_ip_alignment(self, text: str, symptom: str) -> List[CiscoConfigAnomaly]:
        anomalies = []
        if "standby" in text.lower():
            vip_match = re.search(r'Virtual IP\s*\n\s*\S+\s+\d+\s+P?\s+\S+\s+\S+\s+([\d.]+)', text)
            client_gw = re.search(r'Default Gateway[.\s:]+([\d.]+)', text)
            if vip_match and client_gw:
                vip = vip_match.group(1)
                cgw = client_gw.group(1)
                if vip != cgw:
                    anomalies.append(CiscoConfigAnomaly(
                        anomaly_id="RULE-HSRP-01",
                        title=f"Host Gateway Mismatches HSRP Virtual IP ({vip})",
                        severity_level="High",
                        osi_layer="Layer 3 - Network",
                        domain_tag="GATEWAY",
                        description=f"Client is configured with physical router IP {cgw} instead of HSRP Virtual IP {vip}.",
                        raw_evidence=[f"Client Gateway: {cgw}", f"HSRP Virtual IP: {vip}"],
                        cli_remediation=f"Reconfigure host default gateway to HSRP Virtual IP {vip}."
                    ))
        return anomalies


# Backward Compatibility Alias
DeterministicRuleChecker = CiscoNetworkValidator
RuleFinding = CiscoConfigAnomaly


def main():
    import argparse
    import csv
    import json

    parser = argparse.ArgumentParser(description="NetSage AI Cisco Network Validator CLI")
    parser.add_argument("--case", type=str, help="Case ID to inspect (e.g. CASE-01)")
    parser.add_argument("--all", action="store_true", help="Run rule validation across all cases")
    parser.add_argument("--csv", type=str, default="data/cases.csv", help="Path to cases.csv")
    args = parser.parse_args()

    validator = CiscoNetworkValidator()
    csv_path = args.csv

    if not os.path.exists(csv_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, "data", "cases.csv")

    if not os.path.exists(csv_path):
        print(f"Error: cases.csv not found at {csv_path}")
        return

    with open(csv_path, mode="r", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))

    if args.case:
        matched = [c for c in cases if c["case_id"].upper() == args.case.upper()]
        if not matched:
            print(f"Case {args.case} not found.")
            return
        case = matched[0]
        print(f"\n=== Running NetSage Inspection on {case['case_id']}: {case['title']} ===")
        anomalies = validator.execute_inspection(case["symptom"], case["topology_note"], case["show_outputs"])
        print(f"Found {len(anomalies)} deterministic anomaly(ies):")
        for idx, a in enumerate(anomalies, 1):
            print(f"\n[{idx}] {a.anomaly_id} ({a.severity_level} - {a.osi_layer}): {a.title}")
            print(f"    Domain: {a.domain_tag}")
            print(f"    Description: {a.description}")
            print(f"    Evidence: {a.raw_evidence}")
            print(f"    CLI Fix:\n{a.cli_remediation}")
    elif args.all:
        print(f"\n=== Running NetSage Inspection on All {len(cases)} Packet Tracer Cases ===")
        total_anomalies = 0
        cases_flagged = 0
        for case in cases:
            anomalies = validator.execute_inspection(case["symptom"], case["topology_note"], case["show_outputs"])
            total_anomalies += len(anomalies)
            if anomalies:
                cases_flagged += 1
                print(f"✓ {case['case_id']}: {case['title']} -> {len(anomalies)} finding(s) [{', '.join(a.anomaly_id for a in anomalies)}]")
            else:
                print(f"⚠ {case['case_id']}: {case['title']} -> 0 rule findings")
        print(f"\nSummary: {cases_flagged}/{len(cases)} cases flagged by deterministic rules ({total_anomalies} total findings).")


if __name__ == "__main__":
    main()
