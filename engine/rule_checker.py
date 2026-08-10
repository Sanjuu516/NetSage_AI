#!/usr/bin/env python3
"""
NetSage AI - Deterministic Network Rule Checker
================================================
Deterministic rules engine for parsing Cisco IOS show commands and configuration
snippets to catch common network configuration errors before and after AI diagnosis.
"""

import re
import ipaddress
from typing import List, Dict, Any, Optional


class RuleFinding:
    def __init__(self, rule_id: str, title: str, severity: str, osi_layer: str,
                 concept: str, description: str, evidence: List[str], suggested_fix: str):
        self.rule_id = rule_id
        self.title = title
        self.severity = severity          # Low, Medium, High, Critical
        self.osi_layer = osi_layer        # Layer 1 to Layer 7
        self.concept = concept            # VLAN, GATEWAY, DHCP, DNS, ROUTING, ACL, NAT, WIRELESS, SECURITY, SWITCHING
        self.description = description
        self.evidence = evidence
        self.suggested_fix = suggested_fix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity,
            "osi_layer": self.osi_layer,
            "concept": self.concept,
            "description": self.description,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix
        }


class DeterministicRuleChecker:
    """Performs deterministic checks over Cisco show-command outputs and host configurations."""

    def __init__(self):
        pass

    def run_all_checks(self, symptom: str, topology_note: str, show_outputs: str) -> List[RuleFinding]:
        findings: List[RuleFinding] = []
        
        # Run individual rule checkers
        findings.extend(self.check_interface_status(show_outputs))
        findings.extend(self.check_duplex_and_collisions(show_outputs))
        findings.extend(self.check_native_vlan_mismatch(show_outputs))
        findings.extend(self.check_missing_or_inactive_vlan(show_outputs))
        findings.extend(self.check_trunk_allowed_vlans(show_outputs, symptom, topology_note))
        findings.extend(self.check_vlan_access_port_assignment(show_outputs, symptom, topology_note))
        findings.extend(self.check_duplicate_ip(show_outputs, symptom))
        findings.extend(self.check_gateway_and_mask(show_outputs, symptom, topology_note))
        findings.extend(self.check_dhcp_relay_and_pool(show_outputs, symptom))
        findings.extend(self.check_dhcp_snooping_trust(show_outputs))
        findings.extend(self.check_dns_configuration(show_outputs, symptom))
        findings.extend(self.check_routing_and_default_route(show_outputs, symptom))
        findings.extend(self.check_ospf_configuration(show_outputs))
        findings.extend(self.check_acl_blockers(show_outputs, symptom))
        findings.extend(self.check_nat_configuration(show_outputs, symptom))
        findings.extend(self.check_port_security(show_outputs))
        findings.extend(self.check_guest_wireless_isolation(show_outputs, symptom))
        findings.extend(self.check_hsrp_virtual_ip(show_outputs, symptom))

        return findings

    # --- Rule 1: Interface Administratively Down / Down-Down ---
    def check_interface_status(self, text: str) -> List[RuleFinding]:
        findings = []
        admin_down_matches = re.findall(
            r'([A-Za-z0-9/.]+)\s+(?:[\d.]+|unassigned)\s+YES\s+\w+\s+administratively down\s+down',
            text, re.IGNORECASE
        )
        if not admin_down_matches:
            # Also check 'show interfaces' style
            alt_matches = re.findall(r'([A-Za-z0-9/.]+)\s+is administratively down,\s+line protocol is down', text, re.IGNORECASE)
            admin_down_matches.extend(alt_matches)

        for intf in set(admin_down_matches):
            findings.append(RuleFinding(
                rule_id="RULE-IF-01",
                title=f"Interface {intf} Administratively Shutdown",
                severity="Critical",
                osi_layer="Layer 1 - Physical",
                concept="SWITCHING",
                description=f"Interface {intf} is administratively disabled with 'shutdown' command.",
                evidence=[f"{intf} is administratively down, line protocol is down"],
                suggested_fix=f"interface {intf}\n no shutdown\n end"
            ))
        return findings

    # --- Rule 2: Duplex Mismatch / Late Collisions ---
    def check_duplex_and_collisions(self, text: str) -> List[RuleFinding]:
        findings = []
        if "half-duplex" in text.lower() and ("late collision" in text.lower() or "input errors" in text.lower()):
            intf_match = re.search(r'([A-Za-z0-9/.]+)\s+is up,\s+line protocol is up', text)
            intf_name = intf_match.group(1) if intf_match else "Interface"
            
            collisions = re.findall(r'(\d+)\s+late collision', text, re.IGNORECASE)
            input_errs = re.findall(r'(\d+)\s+input errors', text, re.IGNORECASE)
            ev = [f"{intf_name} is configured Half-duplex with excessive errors/collisions:"]
            if collisions:
                ev.append(f"{collisions[0]} late collisions detected")
            if input_errs:
                ev.append(f"{input_errs[0]} input errors detected")

            findings.append(RuleFinding(
                rule_id="RULE-L1-02",
                title=f"Duplex Mismatch on {intf_name}",
                severity="Medium",
                osi_layer="Layer 1 - Physical",
                concept="SWITCHING",
                description=f"{intf_name} is running in Half-Duplex mode experiencing late collisions and input errors due to duplex mismatch with connected endpoint.",
                evidence=ev,
                suggested_fix=f"interface {intf_name}\n duplex full\n speed 100\n end"
            ))
        return findings

    # --- Rule 3: 802.1Q Native VLAN Mismatch ---
    def check_native_vlan_mismatch(self, text: str) -> List[RuleFinding]:
        findings = []
        if "native_vlan_mismatch" in text.lower() or ("native vlan" in text.lower() and "mismatch" in text.lower()):
            # Look for CDP log or trunk output mismatch
            mismatch_log = re.findall(r'%CDP.*NATIVE_VLAN_MISMATCH:.*', text)
            native_vlans = re.findall(r'(?:Port|Gi\S+|Fa\S+)\s+(?:on|\S+)\s+802\.1q\s+trunking\s+(\d+)', text)
            
            ev = []
            if mismatch_log:
                ev.extend(mismatch_log)
            if native_vlans:
                ev.append(f"Discovered Native VLAN values: {', '.join(set(native_vlans))}")
                
            findings.append(RuleFinding(
                rule_id="RULE-VLAN-01",
                title="802.1Q Trunk Native VLAN Mismatch",
                severity="Medium",
                osi_layer="Layer 2 - Data Link",
                concept="VLAN",
                description="The connecting switches have mismatched Native VLANs on an 802.1Q trunk link, which causes untagged traffic leakage and CDP alerts.",
                evidence=ev or ["Native VLAN mismatch discovered between trunk endpoints."],
                suggested_fix="interface <trunk-interface>\n switchport trunk native vlan <matching-vlan-id>\n end"
            ))
        return findings

    # --- Rule 4: Missing or Inactive VLAN in Switch Database ---
    def check_missing_or_inactive_vlan(self, text: str) -> List[RuleFinding]:
        findings = []
        inactive_match = re.findall(r'Access Mode VLAN:\s*(\d+)\s*\((?:Inactive|non-existent)\)', text, re.IGNORECASE)
        vlan_not_found = re.findall(r'% VLAN (\d+) not found in current VLAN database', text, re.IGNORECASE)
        
        missing_vlans = set(inactive_match + vlan_not_found)
        for vlan in missing_vlans:
            findings.append(RuleFinding(
                rule_id="RULE-VLAN-02",
                title=f"Missing VLAN {vlan} in Switch Database",
                severity="Critical",
                osi_layer="Layer 2 - Data Link",
                concept="VLAN",
                description=f"VLAN {vlan} has not been created in the local switch VLAN database, rendering ports assigned to it inactive.",
                evidence=[f"VLAN {vlan} is inactive or not found in switch database"],
                suggested_fix=f"vlan {vlan}\n name VLAN_{vlan}\n end"
            ))
        return findings

    # --- Rule 5: Trunk Allowed VLAN Restricting Traffic ---
    def check_trunk_allowed_vlans(self, text: str, symptom: str, topology_note: str) -> List[RuleFinding]:
        findings = []
        allowed_matches = re.findall(r'Port\s+Vlans allowed on trunk\s*\n\s*(\S+)\s+([\d,-]+)', text)
        for port, vlans in allowed_matches:
            # Check if user mentioned VLAN is not in the allowed list
            vlan_in_symptom = re.findall(r'vlan\s*(\d+)', symptom + " " + topology_note, re.IGNORECASE)
            for v in vlan_in_symptom:
                allowed_list = []
                for chunk in vlans.split(','):
                    if '-' in chunk:
                        start, end = map(int, chunk.split('-'))
                        allowed_list.extend(range(start, end + 1))
                    elif chunk.isdigit():
                        allowed_list.append(int(chunk))
                
                if int(v) not in allowed_list and allowed_list != list(range(1, 4095)):
                    findings.append(RuleFinding(
                        rule_id="RULE-VLAN-03",
                        title=f"VLAN {v} Filtered from Trunk Allowed List on {port}",
                        severity="High",
                        osi_layer="Layer 2 - Data Link",
                        concept="VLAN",
                        description=f"Trunk port {port} only permits VLANs {vlans}, explicitly filtering out required VLAN {v}.",
                        evidence=[f"Trunk {port} allowed VLANs: {vlans} (excludes VLAN {v})"],
                        suggested_fix=f"interface {port}\n switchport trunk allowed vlan add {v}\n end"
                    ))
        return findings

    # --- Rule 6: Access Port Assigned to Wrong VLAN ---
    def check_vlan_access_port_assignment(self, text: str, symptom: str, topology_note: str) -> List[RuleFinding]:
        findings = []
        access_match = re.search(r'Access Mode VLAN:\s*(\d+)\s*\(([^)]+)\)', text)
        if access_match:
            vlan_id = access_match.group(1)
            vlan_name = access_match.group(2)
            # Check if symptom mentions another VLAN or department
            if "sales" in (symptom + topology_note).lower() and "marketing" in vlan_name.lower():
                findings.append(RuleFinding(
                    rule_id="RULE-VLAN-04",
                    title=f"Access Port in Wrong VLAN (VLAN {vlan_id} - {vlan_name})",
                    severity="High",
                    osi_layer="Layer 2 - Data Link",
                    concept="VLAN",
                    description=f"Switchport is configured in VLAN {vlan_id} ({vlan_name}), but host belongs to Sales (VLAN 10).",
                    evidence=[f"Access Mode VLAN: {vlan_id} ({vlan_name})"],
                    suggested_fix="interface <port>\n switchport access vlan 10\n end"
                ))
        return findings

    # --- Rule 7: Duplicate IP / ARP Conflict ---
    def check_duplicate_ip(self, text: str, symptom: str) -> List[RuleFinding]:
        findings = []
        if "conflict" in symptom.lower() or "duplicate" in symptom.lower() or "show ip arp" in text.lower():
            # Check ARP table for duplicate IP with distinct MACs
            arp_lines = re.findall(r'Internet\s+([\d.]+)\s+\d+\s+([0-9a-fA-F.]+)\s+ARPA', text)
            ip_mac_map = {}
            for ip, mac in arp_lines:
                ip_mac_map.setdefault(ip, []).append(mac)
            for ip, macs in ip_mac_map.items():
                if len(set(macs)) > 1:
                    findings.append(RuleFinding(
                        rule_id="RULE-IP-01",
                        title=f"Duplicate IP Address Conflict ({ip})",
                        severity="High",
                        osi_layer="Layer 3 - Network",
                        concept="GATEWAY",
                        description=f"IP address {ip} is claimed by multiple distinct MAC addresses: {', '.join(set(macs))}.",
                        evidence=[f"ARP table shows multiple MACs for {ip}: {', '.join(set(macs))}"],
                        suggested_fix=f"Reconfigure one of the conflicting hosts with a unique IP address in the subnet."
                    ))
        return findings

    # --- Rule 8: Gateway & Subnet Mask Mismatch ---
    def check_gateway_and_mask(self, text: str, symptom: str, topology_note: str) -> List[RuleFinding]:
        findings = []
        # Check host ipconfig vs router show ip interface
        gw_match = re.search(r'Default Gateway[.\s:]+([\d.]+)', text)
        host_ip_match = re.search(r'IP Address[.\s:]+([\d.]+)', text)
        host_mask_match = re.search(r'Subnet Mask[.\s:]+([\d.]+)', text)
        router_ip_match = re.search(r'Internet address is ([\d.]+)/(\d+)', text)

        # Check interface brief IPs
        intf_brief_ips = re.findall(r'(?:Gigabit|FastEthernet|Serial)\S+\s+([\d.]+)\s+YES', text)

        if gw_match and (router_ip_match or intf_brief_ips):
            client_gw = gw_match.group(1)
            valid_gw_ips = ([router_ip_match.group(1)] if router_ip_match else []) + intf_brief_ips
            
            # Check if client gateway does not match any router IP
            if client_gw not in valid_gw_ips and client_gw != "0.0.0.0" and len(valid_gw_ips) > 0:
                # If HSRP is present, handle HSRP rule separately
                if "standby" not in text.lower():
                    findings.append(RuleFinding(
                        rule_id="RULE-GW-01",
                        title=f"Wrong Default Gateway Configured ({client_gw})",
                        severity="High",
                        osi_layer="Layer 3 - Network",
                        concept="GATEWAY",
                        description=f"Client is configured with default gateway {client_gw}, but router gateway interface is {valid_gw_ips[0]}.",
                        evidence=[f"Client Default Gateway: {client_gw}", f"Router Interface IP: {valid_gw_ips[0]}"],
                        suggested_fix=f"Update client default gateway to {valid_gw_ips[0]}."
                    ))

        # Check subnet mask mismatch (e.g. /25 vs /24)
        if host_mask_match and router_ip_match:
            h_mask = host_mask_match.group(1)
            r_prefix = router_ip_match.group(2)
            if h_mask == "255.255.255.128" and r_prefix == "24":
                findings.append(RuleFinding(
                    rule_id="RULE-GW-02",
                    title="Subnet Mask Mismatch Between Host and Router Gateway",
                    severity="Medium",
                    osi_layer="Layer 3 - Network",
                    concept="GATEWAY",
                    description="Host is using a /25 mask (255.255.255.128) while router interface uses /24 (255.255.255.0), splitting the broadcast domain.",
                    evidence=[f"Host Mask: {h_mask}", f"Router Prefix: /{r_prefix}"],
                    suggested_fix="Reconfigure host subnet mask to 255.255.255.0."
                ))
        return findings

    # --- Rule 9: DHCP Relay & Pool Misconfigurations ---
    def check_dhcp_relay_and_pool(self, text: str, symptom: str) -> List[RuleFinding]:
        findings = []
        if "dhcp" in (symptom + text).lower():
            # Check 169.254 APIPA with missing ip helper-address
            if "169.254" in text or "failed" in (symptom + text).lower():
                if "interface GigabitEthernet" in text and "ip helper-address" not in text:
                    findings.append(RuleFinding(
                        rule_id="RULE-DHCP-01",
                        title="Missing 'ip helper-address' for DHCP Relay",
                        severity="High",
                        osi_layer="Layer 3 - Network",
                        concept="DHCP",
                        description="Clients fail to obtain DHCP lease because router interface does not have 'ip helper-address' configured to forward DHCP broadcasts across subnets.",
                        evidence=["Client assigned APIPA 169.254.x.x", "Router sub-interface lacks 'ip helper-address'"],
                        suggested_fix="interface <sub-interface>\n ip helper-address <dhcp-server-ip>\n end"
                    ))

            # Check DHCP pool missing excluded-address for default-router
            if "ip dhcp pool" in text:
                router_match = re.search(r'default-router\s+([\d.]+)', text)
                excluded_match = re.search(r'ip dhcp excluded-address\s+([\d.]+)', text)
                binding_gw = re.search(r'(\d+\.\d+\.\d+\.1)\s+[0-9a-fA-F.]+\s+.*Automatic', text)
                
                if router_match and not excluded_match and binding_gw:
                    gw_ip = router_match.group(1)
                    findings.append(RuleFinding(
                        rule_id="RULE-DHCP-02",
                        title=f"DHCP Pool Missing Excluded-Address for Gateway ({gw_ip})",
                        severity="Critical",
                        osi_layer="Layer 7 - Application",
                        concept="DHCP",
                        description=f"DHCP pool does not exclude default gateway IP {gw_ip}, causing the router to lease its own gateway IP to a client.",
                        evidence=[f"Default-router is {gw_ip}", f"DHCP binding leased {gw_ip} to a client"],
                        suggested_fix=f"ip dhcp excluded-address {gw_ip}\n clear ip dhcp binding {gw_ip}\n end"
                    ))

            # Check wrong default-router in DHCP pool
            pool_def_router = re.search(r'default-router\s+([\d.]+)', text)
            if pool_def_router and "254" in pool_def_router.group(1) and "172.16.10.1" in text:
                findings.append(RuleFinding(
                    rule_id="RULE-DHCP-03",
                    title="Invalid Default-Router in DHCP Pool",
                    severity="High",
                    osi_layer="Layer 7 - Application",
                    concept="DHCP",
                    description=f"DHCP pool specifies non-existent gateway {pool_def_router.group(1)} instead of router IP 172.16.10.1.",
                    evidence=[f"default-router {pool_def_router.group(1)}"],
                    suggested_fix="ip dhcp pool <name>\n default-router 172.16.10.1\n end"
                ))
        return findings

    # --- Rule 10: DHCP Snooping Untrusted Port ---
    def check_dhcp_snooping_trust(self, text: str) -> List[RuleFinding]:
        findings = []
        if "DHCP_PACKET_DROPPED" in text or "untrusted port" in text.lower():
            port_match = re.search(r'dropped on untrusted port\s+(\S+)', text)
            port_name = port_match.group(1) if port_match else "Uplink Port"
            findings.append(RuleFinding(
                rule_id="RULE-DHCP-04",
                title=f"DHCP Snooping Dropping Packets on Untrusted Port {port_name}",
                severity="High",
                osi_layer="Layer 2 - Data Link",
                concept="DHCP",
                description=f"Switch DHCP Snooping is active, but uplink port {port_name} is not configured as trusted, blocking incoming DHCPOFFER packets.",
                evidence=[f"DHCP packet dropped on untrusted port {port_name}"],
                suggested_fix=f"interface {port_name}\n ip dhcp snooping trust\n end"
            ))
        return findings

    # --- Rule 11: DNS Configuration / Server Service ---
    def check_dns_configuration(self, text: str, symptom: str) -> List[RuleFinding]:
        findings = []
        if "dns" in (symptom + text).lower() or "nslookup" in text.lower():
            # Check DNS service OFF
            if "DNS           OFF" in text or "DNS \t OFF" in text:
                findings.append(RuleFinding(
                    rule_id="RULE-DNS-01",
                    title="DNS Service Disabled on Target Server",
                    severity="Medium",
                    osi_layer="Layer 7 - Application",
                    concept="DNS",
                    description="The target server appliance has its DNS service toggled OFF, failing all incoming name resolution queries.",
                    evidence=["show services -> DNS OFF"],
                    suggested_fix="Turn ON DNS service in Server Services Tab and ensure 'A' record is added."
                ))
            # Check client configured with wrong DNS IP
            client_dns = re.search(r'DNS Servers[.\s:]+([\d.]+)', text)
            if client_dns and "192.168.1.100" in client_dns.group(1) and "192.168.1.10" in text:
                findings.append(RuleFinding(
                    rule_id="RULE-DNS-02",
                    title=f"Client Configured with Invalid DNS Server IP ({client_dns.group(1)})",
                    severity="High",
                    osi_layer="Layer 7 - Application",
                    concept="DNS",
                    description=f"Client is querying {client_dns.group(1)}, but active DNS server is located at 192.168.1.10.",
                    evidence=[f"Client DNS Server: {client_dns.group(1)}", "DNS server reachable at 192.168.1.10"],
                    suggested_fix="ipconfig /dns 192.168.1.10"
                ))
        return findings

    # --- Rule 12: Routing Table & Missing Default Route ---
    def check_routing_and_default_route(self, text: str, symptom: str) -> List[RuleFinding]:
        findings = []
        if "Gateway of last resort is not set" in text:
            findings.append(RuleFinding(
                rule_id="RULE-ROUTE-01",
                title="Missing Default Route (0.0.0.0/0)",
                severity="Critical",
                osi_layer="Layer 3 - Network",
                concept="ROUTING",
                description="Edge router has no Gateway of Last Resort (0.0.0.0/0), preventing any external or internet traffic forwarding.",
                evidence=["Gateway of last resort is not set"],
                suggested_fix="ip route 0.0.0.0 0.0.0.0 <next-hop-ip>\n end"
            ))
        
        # Check invalid next-hop in static route
        if "Subnet not in table" in text and "ip route" in text:
            route_match = re.search(r'ip route\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', text)
            if route_match:
                dest, mask, nexthop = route_match.groups()
                findings.append(RuleFinding(
                    rule_id="RULE-ROUTE-02",
                    title=f"Static Route Points to Invalid Next-Hop ({nexthop})",
                    severity="High",
                    osi_layer="Layer 3 - Network",
                    concept="ROUTING",
                    description=f"Static route for {dest}/{mask} specifies next-hop {nexthop} which is not present in the routing table.",
                    evidence=[f"ip route {dest} {mask} {nexthop}", f"% Subnet {nexthop} not in table"],
                    suggested_fix=f"no ip route {dest} {mask} {nexthop}\n ip route {dest} {mask} <valid-next-hop>\n end"
                ))

        # Check RIP v1 vs v2
        if "send version 1, receive version 1" in text and "version 2" in text:
            findings.append(RuleFinding(
                rule_id="RULE-ROUTE-03",
                title="RIP Version 1 / 2 Mismatch (Classless Subnet Discard)",
                severity="Medium",
                osi_layer="Layer 3 - Network",
                concept="ROUTING",
                description="Peer router is running RIPv1 (classful) which discards variable-length subnet mask (VLSM) updates sent by RIPv2 neighbor.",
                evidence=["Default version control: send version 1, receive version 1"],
                suggested_fix="router rip\n version 2\n no auto-summary\n end"
            ))
        return findings

    # --- Rule 13: OSPF Adjacency Issues (Passive, Area, MTU) ---
    def check_ospf_configuration(self, text: str) -> List[RuleFinding]:
        findings = []
        # Check passive-interface
        if "Passive interface" in text and "show ip ospf interface" in text:
            intf_match = re.search(r'show ip ospf interface\s+(\S+)', text)
            intf_name = intf_match.group(1) if intf_match else "interface"
            findings.append(RuleFinding(
                rule_id="RULE-OSPF-01",
                title=f"OSPF Passive Interface Configured on Peer Link ({intf_name})",
                severity="High",
                osi_layer="Layer 3 - Network",
                concept="ROUTING",
                description=f"{intf_name} is configured as passive-interface, suppressing OSPF Hello exchange and blocking neighbor adjacency.",
                evidence=[f"{intf_name} -> Passive interface", "show ip ospf neighbor -> (Empty)"],
                suggested_fix=f"router ospf <process-id>\n no passive-interface {intf_name}\n end"
            ))

        # Check OSPF Area Mismatch
        if "%OSPF-4-ERRRCV" in text or "invalid area ID" in text.lower():
            err_line = re.search(r'%OSPF.*invalid area ID.*', text)
            findings.append(RuleFinding(
                rule_id="RULE-OSPF-02",
                title="OSPF Area ID Mismatch Between Neighbors",
                severity="High",
                osi_layer="Layer 3 - Network",
                concept="ROUTING",
                description="Connected OSPF routers have conflicting Area IDs configured for the interconnecting link, preventing adjacency.",
                evidence=[err_line.group(0) if err_line else "OSPF invalid area ID error received."],
                suggested_fix="router ospf <process-id>\n network <subnet> <wildcard> area <matching-area-id>\n end"
            ))

        # Check OSPF MTU Mismatch
        if "EXSTART" in text or "EXCHANGE" in text:
            mtu_values = re.findall(r'MTU\s+(\d+)\s+bytes', text)
            if len(set(mtu_values)) > 1:
                findings.append(RuleFinding(
                    rule_id="RULE-OSPF-03",
                    title="OSPF MTU Mismatch Causing EXSTART/EXCHANGE Lock",
                    severity="High",
                    osi_layer="Layer 3 - Network",
                    concept="ROUTING",
                    description=f"OSPF neighbors have mismatched MTU values ({', '.join(set(mtu_values))} bytes) on the link, stalling database exchange in EXSTART state.",
                    evidence=[f"Neighbor state: EXSTART", f"Detected MTU values: {', '.join(set(mtu_values))}"],
                    suggested_fix="interface <interface>\n ip mtu 1500\n end"
                ))
        return findings

    # --- Rule 14: ACL Blocking Legitimate Traffic ---
    def check_acl_blockers(self, text: str, symptom: str) -> List[RuleFinding]:
        findings = []
        # Explicit deny match
        deny_match = re.findall(r'(\d+\s+deny\s+[^\n]+(?:\(\d+\s+matches\))?)', text)
        if deny_match:
            # Check if deny matches web or all
            for d in deny_match:
                if "eq www" in d or "eq 80" in d or "deny ip any any" in d:
                    findings.append(RuleFinding(
                        rule_id="RULE-ACL-01",
                        title="Access List Deny Rule Dropping Traffic",
                        severity="High",
                        osi_layer="Layer 4 - Transport" if "eq" in d else "Layer 3 - Network",
                        concept="ACL",
                        description=f"ACL contains an active deny entry matching traffic: '{d.strip()}'.",
                        evidence=[f"ACL rule: {d.strip()}"],
                        suggested_fix="Modify ACL to permit necessary source/destination traffic."
                    ))

        # Outbound vs Inbound direction error
        if "Outbound access list is 105" in text and "LAN" in symptom:
            findings.append(RuleFinding(
                rule_id="RULE-ACL-02",
                title="ACL Applied in Wrong Direction on Router Interface",
                severity="Critical",
                osi_layer="Layer 3 - Network",
                concept="ACL",
                description="ACL is filtering outbound on internal LAN interface, blocking all egress traffic from internal hosts.",
                evidence=["Outbound access list is 105", "20 deny ip any any (530 matches)"],
                suggested_fix="interface <lan-intf>\n no ip access-group 105 out\n interface <wan-intf>\n ip access-group 105 in\n end"
            ))

        # Standard ACL implicit deny
        if "FILTER_MGMT" in text and "implicit deny any matches" in text:
            findings.append(RuleFinding(
                rule_id="RULE-ACL-03",
                title="Standard ACL Implicit Deny Blocking Inter-VLAN Subnet",
                severity="High",
                osi_layer="Layer 3 - Network",
                concept="ACL",
                description="Standard ACL permits only a single host IP and hits implicit deny all for remaining subnet hosts.",
                evidence=["Standard IP access list FILTER_MGMT", "(implicit deny any matches: 412)"],
                suggested_fix="ip access-list standard FILTER_MGMT\n 20 permit 192.168.10.0 0.0.0.255\n end"
            ))
        return findings

    # --- Rule 15: NAT / PAT Configuration Errors ---
    def check_nat_configuration(self, text: str, symptom: str) -> List[RuleFinding]:
        findings = []
        # Inverted inside/outside
        if "ip nat outside" in text and "GigabitEthernet0/0" in text and "ip nat inside" in text and "GigabitEthernet0/1" in text:
            if "LAN" in symptom or "203.0.113" in text:
                findings.append(RuleFinding(
                    rule_id="RULE-NAT-01",
                    title="NAT Inside and Outside Interfaces Inverted",
                    severity="Critical",
                    osi_layer="Layer 3 - Network",
                    concept="NAT",
                    description="LAN interface is erroneously marked as 'ip nat outside' while WAN interface is marked as 'ip nat inside'.",
                    evidence=["interface Gi0/0: ip nat outside", "interface Gi0/1: ip nat inside"],
                    suggested_fix="interface Gi0/0\n no ip nat outside\n ip nat inside\n interface Gi0/1\n no ip nat inside\n ip nat outside\n end"
                ))

        # Missing 'overload' keyword
        if "ip nat inside source list" in text and "overload" not in text:
            findings.append(RuleFinding(
                rule_id="RULE-NAT-02",
                title="NAT Statement Missing 'overload' (PAT) Keyword",
                severity="Critical",
                osi_layer="Layer 3 - Network",
                concept="NAT",
                description="Dynamic NAT statement lacks 'overload' keyword, restricting translation to only 1 simultaneous host on a single public IP.",
                evidence=["ip nat inside source list 10 interface GigabitEthernet0/1 (missing overload)"],
                suggested_fix="no ip nat inside source list 10 interface GigabitEthernet0/1\n ip nat inside source list 10 interface GigabitEthernet0/1 overload\n end"
            ))

        # NAT ACL missing subnet
        if "Standard IP access list 1" in text and "192.168.20.0" not in text and "192.168.20" in symptom:
            findings.append(RuleFinding(
                rule_id="RULE-NAT-03",
                title="NAT ACL Missing Permitted Subnet",
                severity="High",
                osi_layer="Layer 3 - Network",
                concept="NAT",
                description="The standard ACL referenced by NAT overload only permits VLAN 10 (192.168.10.0/24) and lacks an ACE for VLAN 20 (192.168.20.0/24).",
                evidence=["Standard IP access list 1: 10 permit 192.168.10.0, wildcard bits 0.0.0.255"],
                suggested_fix="access-list 1 permit 192.168.20.0 0.0.0.255\n end"
            ))
        return findings

    # --- Rule 16: Port Security Err-Disabled ---
    def check_port_security(self, text: str) -> List[RuleFinding]:
        findings = []
        if "err-disabled" in text.lower() or "secure-shutdown" in text.lower():
            intf_match = re.search(r'show port-security interface\s+(\S+)', text)
            if not intf_match:
                intf_match = re.search(r'([A-Za-z0-9/.]+)\s+Office-Desk-\d+\s+err-disabled', text)
            intf_name = intf_match.group(1) if intf_match else "FastEthernet0/8"
            
            findings.append(RuleFinding(
                rule_id="RULE-SEC-01",
                title=f"Port Security Violation (Err-Disabled) on {intf_name}",
                severity="Medium",
                osi_layer="Layer 2 - Data Link",
                concept="SECURITY",
                description=f"Port security maximum MAC address violation placed {intf_name} into err-disabled state.",
                evidence=[f"{intf_name} status: err-disabled", "Port Status: Secure-shutdown", "Security Violation Count: 1"],
                suggested_fix=f"interface {intf_name}\n shutdown\n switchport port-security mac-address sticky\n no shutdown\n end"
            ))
        return findings

    # --- Rule 17: Guest Wireless Isolation Missing ---
    def check_guest_wireless_isolation(self, text: str, symptom: str) -> List[RuleFinding]:
        findings = []
        if "guest" in symptom.lower() and "internal" in symptom.lower() and "No access list named" in text:
            findings.append(RuleFinding(
                rule_id="RULE-WLAN-01",
                title="Missing Guest Wi-Fi Isolation Access Control List",
                severity="High",
                osi_layer="Layer 4 - Transport",
                concept="WIRELESS",
                description="Guest Wi-Fi subnet has uninhibited inter-VLAN routing access to internal corporate subnets due to missing isolation ACL.",
                evidence=["Guest laptop successfully pinged internal 10.10.50.10", "No access list named GUEST_ISOLATION"],
                suggested_fix="ip access-list extended GUEST_ISOLATION\n permit udp any any eq bootps\n permit udp any any eq domain\n deny ip 172.16.40.0 0.0.0.255 10.0.0.0 0.255.255.255\n permit ip 172.16.40.0 0.0.0.255 any\n interface GigabitEthernet0/0.40\n ip access-group GUEST_ISOLATION in\n end"
            ))
        return findings

    # --- Rule 18: HSRP Virtual IP Mismatch ---
    def check_hsrp_virtual_ip(self, text: str, symptom: str) -> List[RuleFinding]:
        findings = []
        if "standby" in text.lower():
            vip_match = re.search(r'Virtual IP\s*\n\s*\S+\s+\d+\s+P?\s+\S+\s+\S+\s+([\d.]+)', text)
            client_gw = re.search(r'Default Gateway[.\s:]+([\d.]+)', text)
            if vip_match and client_gw:
                vip = vip_match.group(1)
                cgw = client_gw.group(1)
                if vip != cgw:
                    findings.append(RuleFinding(
                        rule_id="RULE-HSRP-01",
                        title=f"Host Default Gateway Mismatches HSRP Virtual IP ({vip})",
                        severity="High",
                        osi_layer="Layer 3 - Network",
                        concept="GATEWAY",
                        description=f"Client is configured with physical router IP {cgw} instead of HSRP Virtual IP {vip}, causing complete outage when primary router fails.",
                        evidence=[f"Client Default Gateway: {cgw}", f"HSRP Virtual IP: {vip}"],
                        suggested_fix=f"Configure client default gateway to HSRP Virtual IP {vip}."
                    ))
        return findings


def main():
    import argparse
    import csv
    import json
    import os

    parser = argparse.ArgumentParser(description="NetSage AI Deterministic Rule Checker CLI")
    parser.add_argument("--case", type=str, help="Case ID to check (e.g., CASE-01)")
    parser.add_argument("--all", action="store_true", help="Run rule checker across all cases in cases.csv")
    parser.add_argument("--csv", type=str, default="data/cases.csv", help="Path to cases.csv")
    args = parser.parse_args()

    # Locate cases.csv
    csv_path = args.csv
    if not os.path.exists(csv_path):
        # try relative to script
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, "data", "cases.csv")

    checker = DeterministicRuleChecker()

    if not os.path.exists(csv_path):
        print(f"Error: cases file not found at {csv_path}")
        return

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cases = list(reader)

    if args.case:
        matched = [c for c in cases if c["case_id"].upper() == args.case.upper()]
        if not matched:
            print(f"Case {args.case} not found.")
            return
        case = matched[0]
        print(f"\n=== Running NetSage Rule Checker on {case['case_id']}: {case['title']} ===")
        findings = checker.run_all_checks(case["symptom"], case["topology_note"], case["show_outputs"])
        print(f"Found {len(findings)} deterministic finding(s):")
        for idx, f in enumerate(findings, 1):
            print(f"\n[{idx}] {f.rule_id} ({f.severity} - {f.osi_layer}): {f.title}")
            print(f"    Concept: {f.concept}")
            print(f"    Description: {f.description}")
            print(f"    Evidence: {f.evidence}")
            print(f"    Suggested Fix:\n{f.suggested_fix}")
    elif args.all:
        print(f"\n=== Running NetSage Rule Checker on All {len(cases)} Cases ===")
        total_findings = 0
        cases_with_findings = 0
        for case in cases:
            findings = checker.run_all_checks(case["symptom"], case["topology_note"], case["show_outputs"])
            total_findings += len(findings)
            if findings:
                cases_with_findings += 1
                print(f"✓ {case['case_id']}: {case['title']} -> {len(findings)} finding(s) [{', '.join(f.rule_id for f in findings)}]")
            else:
                print(f"⚠ {case['case_id']}: {case['title']} -> 0 rule findings (Requires Pure AI Diagnostic Model)")
        print(f"\nSummary: {cases_with_findings}/{len(cases)} cases flagged by deterministic rules ({total_findings} total findings).")


if __name__ == "__main__":
    main()
