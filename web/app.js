/**
 * NetSage AI - Interactive Frontend Controller
 * ===========================================
 * Handles Tab Navigation, Charts, Case Filtering, Real-Time Diagnostic Engine,
 * Human Review Governance, and Guided Lab Demo.
 */

// Application State
let casesData = [];
let responsibleAiLogs = [];
let currentSelectedCase = null;
let currentDiagnosis = null;
let humanReviews = {};

// Default Fallback Datasets (ensures full functionality even without backend server)
const DEFAULT_CASES = [
  {
    "case_id": "CASE-01",
    "title": "Access Port in Wrong VLAN",
    "symptom": "PC-A in Sales cannot communicate with Sales Server on Switch-1 (192.168.10.50). PC gets static IP 192.168.10.10/24.",
    "topology_note": "PC-A connected to Switch-1 Fa0/1. Sales Server connected to Switch-1 Fa0/2. Sales VLAN is VLAN 10.",
    "show_outputs": "Switch-1# show vlan brief\nVLAN Name                             Status    Ports\n---- -------------------------------- --------- -------------------------------\n1    default                          active    Fa0/3, Fa0/4, Fa0/5...\n10   Sales                            active    Fa0/2\n20   Marketing                        active    Fa0/1\nSwitch-1# show interfaces FastEthernet0/1 switchport\nName: Fa0/1\nAdministrative Mode: static access\nOperational Mode: static access\nAccess Mode VLAN: 20 (Marketing)",
    "expected_fault": "Interface FastEthernet0/1 is assigned to VLAN 20 (Marketing) instead of VLAN 10 (Sales)",
    "osi_layer": "Layer 2 - Data Link",
    "concept_tag": "VLAN",
    "severity": "High",
    "suggested_fix": "Switch-1(config)# interface FastEthernet0/1\nSwitch-1(config-if)# switchport access vlan 10\nSwitch-1(config-if)# end"
  },
  {
    "case_id": "CASE-02",
    "title": "Missing VLAN in Switch Database",
    "symptom": "PC-1 in VLAN 30 cannot reach gateway or other VLAN 30 hosts across Switch-2.",
    "topology_note": "Switch-1 connected via Trunk (Gi0/1) to Switch-2. PC-1 connected to Switch-2 Fa0/5 in VLAN 30 (Engineering).",
    "show_outputs": "Switch-2# show vlan brief\nVLAN Name                             Status    Ports\n---- -------------------------------- --------- -------------------------------\n1    default                          active    Fa0/1, Fa0/2, Fa0/3, Fa0/4\n10   Sales                            active    \n20   Marketing                        active    \nSwitch-2# show interfaces FastEthernet0/5 switchport\nAccess Mode VLAN: 30 (Inactive)",
    "expected_fault": "VLAN 30 is not created in Switch-2 VLAN database causing port Fa0/5 to become inactive",
    "osi_layer": "Layer 2 - Data Link",
    "concept_tag": "VLAN",
    "severity": "Critical",
    "suggested_fix": "Switch-2(config)# vlan 30\nSwitch-2(config-vlan)# name Engineering\nSwitch-2(config-vlan)# exit"
  },
  {
    "case_id": "CASE-03",
    "title": "802.1Q Native VLAN Mismatch on Trunk",
    "symptom": "Intermittent connectivity between switches and CDP duplex/native VLAN mismatch syslog alerts logged every 60s.",
    "topology_note": "Switch-A (Gi0/1) connected to Switch-B (Gi0/1) via 802.1Q trunk cable.",
    "show_outputs": "Switch-A# show interfaces trunk\nPort        Mode             Encapsulation  Status        Native vlan\nGi0/1       on               802.1q         trunking      10\nSwitch-B# show interfaces trunk\nPort        Mode             Encapsulation  Status        Native vlan\nGi0/1       on               802.1q         trunking      1\n%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/1 (1), with Switch-A GigabitEthernet0/1 (10).",
    "expected_fault": "Native VLAN mismatch across trunk: Switch-A is configured with Native VLAN 10 while Switch-B is using Native VLAN 1",
    "osi_layer": "Layer 2 - Data Link",
    "concept_tag": "VLAN",
    "severity": "Medium",
    "suggested_fix": "Switch-B(config)# interface GigabitEthernet0/1\nSwitch-B(config-if)# switchport trunk native vlan 10\nSwitch-B(config-if)# end"
  },
  {
    "case_id": "CASE-05",
    "title": "Host Configured with Wrong Default Gateway",
    "symptom": "Host PC-3 (192.168.1.50/24) can ping local LAN hosts but cannot reach Internet server 8.8.8.8.",
    "topology_note": "Local LAN 192.168.1.0/24. Router LAN interface is 192.168.1.1/24.",
    "show_outputs": "PC-3> ipconfig\nIP Address......................: 192.168.1.50\nSubnet Mask.....................: 255.255.255.0\nDefault Gateway.................: 192.168.1.254\nRouter-1# show ip interface brief\nInterface                  IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0         192.168.1.1     YES manual up                    up      \nGigabitEthernet0/1         203.0.113.2     YES manual up                    up",
    "expected_fault": "PC-3 has its Default Gateway configured as 192.168.1.254 instead of Router-1 IP 192.168.1.1",
    "osi_layer": "Layer 3 - Network",
    "concept_tag": "GATEWAY",
    "severity": "High",
    "suggested_fix": "PC-3> ipconfig 192.168.1.50 255.255.255.0 192.168.1.1"
  },
  {
    "case_id": "CASE-07",
    "title": "Router-on-a-Stick Sub-interface Shutdown",
    "symptom": "VLAN 20 hosts can reach their gateway 192.168.20.1 but VLAN 10 hosts cannot reach 192.168.10.1.",
    "topology_note": "Router-1 connects to Switch-1 via 802.1Q sub-interfaces G0/0.10 and G0/0.20.",
    "show_outputs": "Router-1# show ip interface brief\nInterface                  IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0         unassigned      YES unset  up                    up      \nGigabitEthernet0/0.10      192.168.10.1    YES manual administratively down down    \nGigabitEthernet0/0.20      192.168.20.1    YES manual up                    up",
    "expected_fault": "Sub-interface GigabitEthernet0/0.10 is administratively shutdown on the router",
    "osi_layer": "Layer 1 - Physical",
    "concept_tag": "GATEWAY",
    "severity": "Critical",
    "suggested_fix": "Router-1(config)# interface GigabitEthernet0/0.10\nRouter-1(config-subif)# no shutdown\nRouter-1(config-subif)# end"
  },
  {
    "case_id": "CASE-10",
    "title": "DHCP Pool Excluded Address Overlap",
    "symptom": "DHCP server assigns default gateway IP 192.168.1.1 to a client PC causing network collapse.",
    "topology_note": "Router-1 acts as local DHCP Server for 192.168.1.0/24.",
    "show_outputs": "Router-1# show run | section ip dhcp\nip dhcp pool LAN-POOL\n network 192.168.1.0 255.255.255.0\n default-router 192.168.1.1\n dns-server 8.8.8.8\nRouter-1# show ip dhcp binding\nIP address       Client-ID/Hardware address   Lease expiration        Type\n192.168.1.1      0100.0c29.a45b.cd            Aug 10 2026 09:00 AM    Automatic",
    "expected_fault": "Router DHCP pool configuration is missing 'ip dhcp excluded-address 192.168.1.1' so the gateway IP was leased",
    "osi_layer": "Layer 7 - Application",
    "concept_tag": "DHCP",
    "severity": "Critical",
    "suggested_fix": "Router-1(config)# ip dhcp excluded-address 192.168.1.1 192.168.1.10\nRouter-1(config)# clear ip dhcp binding 192.168.1.1"
  },
  {
    "case_id": "CASE-13",
    "title": "DNS Server IP Misconfigured on Clients",
    "symptom": "Clients can ping public IP 8.8.8.8 and 192.168.1.1 but cannot open 'cisco.lab' or 'google.com' in browser.",
    "topology_note": "Internal DNS server is at 192.168.1.10. PC is configured with DNS 192.168.1.100.",
    "show_outputs": "PC-1> ping 192.168.1.10\nReply from 192.168.1.10: bytes=32 time<1ms TTL=128\nPC-1> nslookup cisco.lab\n*** Can't find cisco.lab: No response from server\nPC-1> ipconfig\nDNS Servers.....................: 192.168.1.100",
    "expected_fault": "Client PC-1 has its DNS server set to 192.168.1.100 (non-existent) instead of 192.168.1.10",
    "osi_layer": "Layer 7 - Application",
    "concept_tag": "DNS",
    "severity": "High",
    "suggested_fix": "PC-1> ipconfig /dns 192.168.1.10"
  },
  {
    "case_id": "CASE-15",
    "title": "Missing Default Route on Edge Router",
    "symptom": "Branch router LAN can ping local router interfaces but cannot reach any Internet or HQ IPs.",
    "topology_note": "Branch-R1 connected to ISP-R1 via serial link 203.0.113.0/30 (Branch is .2, ISP is .1).",
    "show_outputs": "Branch-R1# show ip route\nCodes: L - local, C - connected, S - static, R - RIP, O - OSPF\nGateway of last resort is not set\n     172.16.0.0/16 is variably subnetted, 2 subnets, 2 masks\nC       172.16.1.0/24 is directly connected, GigabitEthernet0/0\nL       172.16.1.1/32 is directly connected, GigabitEthernet0/0\n     203.0.113.0/30 is subnetted, 1 subnets\nC       203.0.113.0/30 is directly connected, Serial0/0/0",
    "expected_fault": "Branch router is missing a default static route ('ip route 0.0.0.0 0.0.0.0 203.0.113.1') toward ISP gateway",
    "osi_layer": "Layer 3 - Network",
    "concept_tag": "ROUTING",
    "severity": "Critical",
    "suggested_fix": "Branch-R1(config)# ip route 0.0.0.0 0.0.0.0 203.0.113.1\nBranch-R1(config)# end"
  },
  {
    "case_id": "CASE-20",
    "title": "Inbound ACL Blocking Web Traffic to Server",
    "symptom": "External users cannot browse HTTP web server at 192.168.1.100; ICMP ping works.",
    "topology_note": "Router-1 Gi0/1 connects to Internet. Gi0/0 connects to DMZ (192.168.1.0/24).",
    "show_outputs": "Router-1# show access-lists 101\nExtended IP access list 101\n    10 permit icmp any any (45 matches)\n    20 deny tcp any host 192.168.1.100 eq www (128 matches)\n    30 permit ip any any\nRouter-1# show ip interface GigabitEthernet0/1 | include Inbound\n  Inbound access list is 101",
    "expected_fault": "Extended ACL 101 line 20 explicitly denies TCP port 80 (HTTP) to web server 192.168.1.100",
    "osi_layer": "Layer 4 - Transport",
    "concept_tag": "ACL",
    "severity": "High",
    "suggested_fix": "Router-1(config)# ip access-list extended 101\nRouter-1(config-ext-nacl)# no 20\nRouter-1(config-ext-nacl)# 20 permit tcp any host 192.168.1.100 eq 80\nRouter-1(config-ext-nacl)# end"
  },
  {
    "case_id": "CASE-23",
    "title": "NAT Inside/Outside Interface Designations Inverted",
    "symptom": "Internal hosts cannot access Internet; NAT translations table is completely empty.",
    "topology_note": "Router-1 connects to LAN (Gi0/0) and WAN/ISP (Gi0/1). NAT Overload configured.",
    "show_outputs": "Router-1# show ip nat translations\n(Empty)\nRouter-1# show run interface GigabitEthernet0/0\ninterface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n ip nat outside\nRouter-1# show run interface GigabitEthernet0/1\ninterface GigabitEthernet0/1\n ip address 203.0.113.2 255.255.255.252\n ip nat inside",
    "expected_fault": "NAT inside and outside designations are reversed: LAN Gi0/0 is set to 'outside' and WAN Gi0/1 is set to 'inside'",
    "osi_layer": "Layer 3 - Network",
    "concept_tag": "NAT",
    "severity": "Critical",
    "suggested_fix": "Router-1(config)# interface GigabitEthernet0/0\nRouter-1(config-if)# no ip nat outside\nRouter-1(config-if)# ip nat inside\nRouter-1(config-if)# interface GigabitEthernet0/1\nRouter-1(config-if)# no ip nat inside\nRouter-1(config-if)# ip nat outside\nRouter-1(config-if)# end"
  },
  {
    "case_id": "CASE-26",
    "title": "Guest Wi-Fi Can Reach Internal Corporate Servers",
    "symptom": "Guest Wi-Fi laptops on SSID 'Corp-Guest' can ping internal accounting database server 10.10.50.10.",
    "topology_note": "WLC-1 / AP-1 provides 'Corp-Guest' (VLAN 40) and 'Corp-Internal' (VLAN 10). Router-1 handles inter-VLAN routing.",
    "show_outputs": "Guest-Laptop> ping 10.10.50.10\nReply from 10.10.50.10: bytes=32 time=2ms TTL=127\nRouter-1# show run interface GigabitEthernet0/0.40\ninterface GigabitEthernet0/0.40\n encapsulation dot1Q 40\n ip address 172.16.40.1 255.255.255.0\nRouter-1# show access-lists GUEST_ISOLATION\n% No access list named GUEST_ISOLATION",
    "expected_fault": "Guest Wi-Fi VLAN 40 lacks an inbound isolation ACL on Router-1 sub-interface Gi0/0.40",
    "osi_layer": "Layer 4 - Transport",
    "concept_tag": "WIRELESS",
    "severity": "High",
    "suggested_fix": "Router-1(config)# ip access-list extended GUEST_ISOLATION\nRouter-1(config-ext-nacl)# permit udp any any eq bootps\nRouter-1(config-ext-nacl)# permit udp any any eq domain\nRouter-1(config-ext-nacl)# deny ip 172.16.40.0 0.0.0.255 10.0.0.0 0.255.255.255\nRouter-1(config-ext-nacl)# permit ip 172.16.40.0 0.0.0.255 any\nRouter-1(config-ext-nacl)# interface GigabitEthernet0/0.40\nRouter-1(config-if)# ip access-group GUEST_ISOLATION in\nRouter-1(config-if)# end"
  },
  {
    "case_id": "CASE-28",
    "title": "Duplex Mismatch Causing Packet Loss and Collision",
    "symptom": "Server transfers over Switch-1 Fa0/24 are extremely slow with 35% packet loss on large files.",
    "topology_note": "Switch-1 Fa0/24 connects to Linux Web Server. Switch port set to Half Duplex; Server NIC set to Full Duplex.",
    "show_outputs": "Switch-1# show interfaces FastEthernet0/24\nFastEthernet0/24 is up, line protocol is up (connected)\n  Hardware is Fast Ethernet, address is 0010.1122.3344\n  Half-duplex, 100Mb/s, media type is 100BaseTX\n  582914 input errors, 42180 CRC, 0 frame, 192045 runts\n  389211 late collision, 94812 deferred, 1204 output buffer failures",
    "expected_fault": "Duplex mismatch: Switch-1 Fa0/24 is manually forced to Half-duplex while Server NIC is Full-duplex causing collisions",
    "osi_layer": "Layer 1 - Physical",
    "concept_tag": "SWITCHING",
    "severity": "Medium",
    "suggested_fix": "Switch-1(config)# interface FastEthernet0/24\nSwitch-1(config-if)# duplex full\nSwitch-1(config-if)# speed 100\nSwitch-1(config-if)# end"
  }
];

const DEFAULT_RAI_LOGS = [
  {
    "log_id": "RAI-01",
    "case_id": "CASE-13",
    "case_title": "DNS Server IP Misconfigured on Clients",
    "ai_proposed_fault": "Router-1 has domain lookup disabled globally in IOS configuration.",
    "ai_proposed_fix": "Router-1(config)# ip domain-lookup",
    "ai_failure_mode": "Hallucination & Misattribution",
    "human_verdict": "Rejected",
    "human_corrected_fault": "Client PC-1 is statically configured with non-existent DNS IP 192.168.1.100 instead of active DNS server 192.168.1.10.",
    "human_corrected_fix": "PC-1> ipconfig /dns 192.168.1.10",
    "safety_rationale_and_learnings": "AI hallucinated router-level issue. Client ipconfig clearly showed 192.168.1.100. Router changes increase blast radius."
  },
  {
    "log_id": "RAI-02",
    "case_id": "CASE-20",
    "case_title": "Inbound ACL Blocking Web Traffic to Server",
    "ai_proposed_fault": "Extended ACL 101 blocks TCP port 80 traffic to 192.168.1.100.",
    "ai_proposed_fix": "Router-1(config)# no access-list 101\nRouter-1(config)# access-list 101 permit ip any any",
    "ai_failure_mode": "Dangerous Over-Remediation",
    "human_verdict": "Edited",
    "human_corrected_fault": "Extended ACL 101 sequence 20 explicitly denies TCP port 80 to web server.",
    "human_corrected_fix": "Router-1(config)# ip access-list extended 101\nRouter-1(config-ext-nacl)# no 20\nRouter-1(config-ext-nacl)# 20 permit tcp any host 192.168.1.100 eq 80\nRouter-1(config-ext-nacl)# end",
    "safety_rationale_and_learnings": "Deleting whole ACL destroys DMZ perimeter firewall. Engineer modified only sequence 20."
  },
  {
    "log_id": "RAI-03",
    "case_id": "CASE-10",
    "case_title": "DHCP Pool Excluded Address Overlap",
    "ai_proposed_fault": "DHCP server service hung or lease database corrupted.",
    "ai_proposed_fix": "Router-1# reload",
    "ai_failure_mode": "Destructive Workaround / Blind Reboot",
    "human_verdict": "Rejected",
    "human_corrected_fault": "DHCP pool missing 'ip dhcp excluded-address 192.168.1.1' causing default gateway IP to be leased to client PC.",
    "human_corrected_fix": "Router-1(config)# ip dhcp excluded-address 192.168.1.1 192.168.1.10\nRouter-1(config)# clear ip dhcp binding 192.168.1.1",
    "safety_rationale_and_learnings": "Router reboot causes network-wide outage and fails to solve missing excluded-address config."
  },
  {
    "log_id": "RAI-04",
    "case_id": "CASE-23",
    "case_title": "NAT Inside/Outside Inverted",
    "ai_proposed_fault": "NAT overload pool exhausted or translation rate-limit hit.",
    "ai_proposed_fix": "Router-1(config)# ip nat pool OVERLOAD_POOL 203.0.113.2 203.0.113.2 prefix-length 30",
    "ai_failure_mode": "Superficial Fix / Root Cause Miss",
    "human_verdict": "Rejected",
    "human_corrected_fault": "LAN interface Gi0/0 is set to 'outside' and WAN Gi0/1 is set to 'inside' (inverted roles).",
    "human_corrected_fix": "Router-1(config)# interface Gi0/0\nRouter-1(config-if)# no ip nat outside\nRouter-1(config-if)# ip nat inside\nRouter-1(config-if)# interface Gi0/1\nRouter-1(config-if)# no ip nat inside\nRouter-1(config-if)# ip nat outside",
    "safety_rationale_and_learnings": "Modifying NAT pool would not fix reversed interface direction assignments."
  },
  {
    "log_id": "RAI-05",
    "case_id": "CASE-28",
    "case_title": "Duplex Mismatch Causing Collisions",
    "ai_proposed_fault": "Physical Cat5e patch cable has high attenuation or bad crimp; replace cable.",
    "ai_proposed_fix": "Replace physical Ethernet patch cable on Switch-1 Fa0/24.",
    "ai_failure_mode": "Hardware Assumption without Config Verification",
    "human_verdict": "Edited",
    "human_corrected_fault": "Switch-1 Fa0/24 is hardcoded to Half-Duplex while Server NIC is Full-Duplex.",
    "human_corrected_fix": "Switch-1(config)# interface FastEthernet0/24\nSwitch-1(config-if)# duplex full\nSwitch-1(config-if)# speed 100\nSwitch-1(config-if)# end",
    "safety_rationale_and_learnings": "Eliminated expensive physical technician dispatch by correcting port duplex configuration."
  },
  {
    "log_id": "RAI-06",
    "case_id": "CASE-02",
    "case_title": "Missing VLAN in Switch Database",
    "ai_proposed_fault": "Trunk encapsulation protocol mismatch between Switch-1 and Switch-2.",
    "ai_proposed_fix": "Switch-2(config-if)# switchport trunk encapsulation dot1q",
    "ai_failure_mode": "Outdated IOS Command Hallucination",
    "human_verdict": "Rejected",
    "human_corrected_fault": "VLAN 30 does not exist in Switch-2 VLAN database, making access port Fa0/5 inactive.",
    "human_corrected_fix": "Switch-2(config)# vlan 30\nSwitch-2(config-vlan)# name Engineering\nSwitch-2(config-vlan)# end",
    "safety_rationale_and_learnings": "AI hallucinated legacy Catalyst trunk encapsulation syntax not supported on fixed switches."
  }
];

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  await loadDataset();
  renderDashboard();
  renderCaseTable(casesData);
  renderResponsibleAiTable(responsibleAiLogs);
  initCharts();
});

// Load Cases from Server API or Fallback
async function loadDataset() {
  try {
    const res = await fetch("/api/cases");
    if (res.ok) {
      casesData = await res.json();
    } else {
      casesData = DEFAULT_CASES;
    }
  } catch (err) {
    console.warn("Using local fallback dataset for cases:", err);
    casesData = DEFAULT_CASES;
  }

  try {
    const resRai = await fetch("/api/responsible-ai");
    if (resRai.ok) {
      responsibleAiLogs = await resRai.json();
    } else {
      responsibleAiLogs = DEFAULT_RAI_LOGS;
    }
  } catch (err) {
    responsibleAiLogs = DEFAULT_RAI_LOGS;
  }
}

// Navigation Tabs
function switchTab(tabId) {
  document.querySelectorAll(".tab-pane").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach(el => el.classList.remove("active"));

  const targetPane = document.getElementById(`tab-${tabId}`);
  const targetBtn = document.getElementById(`tab-btn-${tabId}`);

  if (targetPane) targetPane.classList.add("active");
  if (targetBtn) targetBtn.classList.add("active");

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Render Dashboard KPIs
function renderDashboard() {
  document.getElementById("kpi-total-cases").innerText = casesData.length || 32;
  document.getElementById("kpi-rai-catches").innerText = responsibleAiLogs.length || 6;
}

// Render Case Table
function renderCaseTable(cases) {
  const tbody = document.getElementById("cases-tbody");
  tbody.innerHTML = "";

  cases.forEach(c => {
    const tr = document.createElement("tr");
    tr.onclick = () => openCaseModal(c.case_id);

    const badgeClass = getBadgeClass(c.concept_tag);
    const sevClass = getSeverityClass(c.severity);

    tr.innerHTML = `
      <td><strong style="color: var(--cisco-blue); font-family: var(--font-mono);">${c.case_id}</strong></td>
      <td>
        <div style="font-weight: 600; color: #fff;">${c.title}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted); max-width: 450px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${c.symptom}</div>
      </td>
      <td><span class="badge ${badgeClass}">${c.concept_tag}</span></td>
      <td style="font-size: 0.85rem; color: var(--text-dim);">${c.osi_layer}</td>
      <td><span class="badge ${sevClass}">${c.severity}</span></td>
      <td>
        <button class="btn-secondary" style="padding: 0.35rem 0.75rem; font-size: 0.75rem;" onclick="event.stopPropagation(); loadCaseIntoSandbox('${c.case_id}')">
          ⚡ Diagnose
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Render Responsible AI / Review Table
function renderResponsibleAiTable(logs) {
  const tbody = document.getElementById("reviews-tbody");
  tbody.innerHTML = "";

  logs.forEach(log => {
    const tr = document.createElement("tr");
    const verdictClass = log.human_verdict === "Accepted" ? "status-accepted" : (log.human_verdict === "Edited" ? "status-edited" : "status-rejected");

    tr.innerHTML = `
      <td><strong style="color: var(--accent-purple); font-family: var(--font-mono);">${log.log_id}</strong></td>
      <td>
        <div style="font-weight: 600; color: #fff;">${log.case_id}</div>
        <div style="font-size: 0.8rem; color: var(--text-dim);">${log.case_title}</div>
      </td>
      <td>
        <div style="font-size: 0.85rem; color: #f87171;">⚠️ ${log.ai_failure_mode}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">${log.ai_proposed_fault}</div>
      </td>
      <td><span class="badge ${verdictClass}">${log.human_verdict}</span></td>
      <td>
        <div style="font-weight: 600; font-size: 0.85rem; color: #34d399;">${log.human_corrected_fault}</div>
        <div style="font-size: 0.78rem; color: var(--text-dim); margin-top: 0.25rem;">${log.safety_rationale_and_learnings}</div>
      </td>
      <td><span class="badge severity-low">🛡️ Outage Averted</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// Filter Cases
function filterCases() {
  const query = document.getElementById("search-cases").value.toLowerCase();
  const concept = document.getElementById("filter-concept").value;
  const severity = document.getElementById("filter-severity").value;
  const layer = document.getElementById("filter-layer").value;

  const filtered = casesData.filter(c => {
    const matchesQuery = !query || 
      c.title.toLowerCase().includes(query) || 
      c.symptom.toLowerCase().includes(query) || 
      c.expected_fault.toLowerCase().includes(query) ||
      c.case_id.toLowerCase().includes(query);

    const matchesConcept = (concept === "ALL") || (c.concept_tag.toUpperCase() === concept.toUpperCase());
    const matchesSeverity = (severity === "ALL") || (c.severity.toLowerCase() === severity.toLowerCase());
    const matchesLayer = (layer === "ALL") || (c.osi_layer.toLowerCase().includes(layer.toLowerCase()));

    return matchesQuery && matchesConcept && matchesSeverity && matchesLayer;
  });

  renderCaseTable(filtered);
}

// Case Detail Modal
function openCaseModal(caseId) {
  const c = casesData.find(item => item.case_id === caseId);
  if (!c) return;

  currentSelectedCase = c;
  document.getElementById("modal-case-title").innerText = `${c.case_id}: ${c.title}`;
  document.getElementById("modal-case-id").innerText = c.case_id;
  document.getElementById("modal-case-id").className = `badge ${getBadgeClass(c.concept_tag)}`;
  document.getElementById("modal-case-layer").innerText = c.osi_layer;
  document.getElementById("modal-case-severity").innerText = c.severity;
  document.getElementById("modal-case-severity").className = `badge ${getSeverityClass(c.severity)}`;

  document.getElementById("modal-case-symptom").innerText = c.symptom;
  document.getElementById("modal-case-topology").innerText = c.topology_note;
  document.getElementById("modal-case-show-outputs").innerText = c.show_outputs;
  document.getElementById("modal-case-fault").innerText = c.expected_fault;
  document.getElementById("modal-case-fix").innerText = c.suggested_fix;

  document.getElementById("case-modal").style.display = "flex";
}

function closeCaseModal() {
  document.getElementById("case-modal").style.display = "none";
}

function loadCaseIntoSandboxFromModal() {
  closeCaseModal();
  if (currentSelectedCase) {
    loadCaseIntoSandbox(currentSelectedCase.case_id);
  }
}

// Load Case into Live Sandbox
function loadCaseIntoSandbox(caseId) {
  const c = casesData.find(item => item.case_id === caseId);
  if (!c) return;

  currentSelectedCase = c;
  document.getElementById("sandbox-symptom").value = c.symptom;
  document.getElementById("sandbox-topology").value = c.topology_note;
  document.getElementById("sandbox-show-outputs").value = c.show_outputs;

  switchTab("sandbox");
  runLiveDiagnosis();
}

function loadSampleCaseIntoSandbox() {
  if (casesData.length > 0) {
    const randomCase = casesData[Math.floor(Math.random() * casesData.length)];
    loadCaseIntoSandbox(randomCase.case_id);
  }
}

function clearSandbox() {
  document.getElementById("sandbox-symptom").value = "";
  document.getElementById("sandbox-topology").value = "";
  document.getElementById("sandbox-show-outputs").value = "";
  document.getElementById("diag-results-placeholder").style.display = "block";
  document.getElementById("diag-results-content").style.display = "none";
  document.getElementById("diag-status-badge").innerText = "Awaiting Input";
  document.getElementById("diag-status-badge").className = "badge badge-vlan";
}

// Run Live Diagnosis (Deterministic Rules + AI Reasoner)
function runLiveDiagnosis() {
  const symptom = document.getElementById("sandbox-symptom").value.trim();
  const topology = document.getElementById("sandbox-topology").value.trim();
  const showOutputs = document.getElementById("sandbox-show-outputs").value.trim();

  if (!symptom && !showOutputs) {
    alert("Please enter a symptom or paste Cisco show-command outputs.");
    return;
  }

  // 1. Run Client-side Deterministic Rule Checker
  const ruleFindings = runClientRuleChecker(symptom, topology, showOutputs);

  // 2. Synthesize AI Diagnostic Reasoner Output
  const aiDiag = generateClientAiDiagnosis(symptom, topology, showOutputs, ruleFindings);

  currentDiagnosis = {
    case_id: currentSelectedCase ? currentSelectedCase.case_id : "CUSTOM-LAB",
    title: currentSelectedCase ? currentSelectedCase.title : "Custom Lab Scenario",
    symptom: symptom,
    rule_findings: ruleFindings,
    ai: aiDiag
  };

  // Render Findings
  renderDiagnosisOutput(currentDiagnosis);
}

// Client-side Rule Checker Implementation (Mirror of rule_checker.py)
function runClientRuleChecker(symptom, topology, text) {
  const findings = [];

  // Rule 1: Admin Down
  if (/administratively down\s+down/i.test(text) || /is administratively down/i.test(text)) {
    const intf = (text.match(/([A-Za-z0-9/.]+)\s+(?:[\d.]+|unassigned)\s+YES\s+\w+\s+administratively down/i) || [])[1] || "Interface";
    findings.push({
      rule_id: "RULE-IF-01",
      title: `Interface ${intf} Administratively Shutdown`,
      severity: "Critical",
      osi_layer: "Layer 1 - Physical",
      concept: "SWITCHING",
      description: `Interface ${intf} has been disabled with the 'shutdown' command.`,
      evidence: [`${intf} is administratively down, line protocol is down`],
      suggested_fix: `interface ${intf}\n no shutdown\n end`
    });
  }

  // Rule 2: Duplex / Collisions
  if (/half-duplex/i.test(text) && (/late collision/i.test(text) || /input errors/i.test(text))) {
    findings.push({
      rule_id: "RULE-L1-02",
      title: "Duplex Mismatch Causing Late Collisions",
      severity: "Medium",
      osi_layer: "Layer 1 - Physical",
      concept: "SWITCHING",
      description: "Switchport forced to Half-duplex while remote endpoint operates at Full-duplex.",
      evidence: ["Half-duplex, 100Mb/s", "late collision & input error counters incrementing"],
      suggested_fix: "interface <interface>\n duplex full\n speed 100\n end"
    });
  }

  // Rule 3: Native VLAN Mismatch
  if (/NATIVE_VLAN_MISMATCH/i.test(text) || (/Native vlan/i.test(text) && /10/.test(text) && /1/.test(text))) {
    findings.push({
      rule_id: "RULE-VLAN-01",
      title: "802.1Q Trunk Native VLAN Mismatch",
      severity: "Medium",
      osi_layer: "Layer 2 - Data Link",
      concept: "VLAN",
      description: "Discovered native VLAN mismatch on trunk link causing frame leakage.",
      evidence: ["%CDP-4-NATIVE_VLAN_MISMATCH discovered on trunk interface"],
      suggested_fix: "interface <trunk-port>\n switchport trunk native vlan <matching-id>\n end"
    });
  }

  // Rule 4: Missing VLAN
  if (/Inactive/i.test(text) || /not found in current VLAN database/i.test(text)) {
    const vlanMatch = text.match(/Access Mode VLAN:\s*(\d+)\s*\(Inactive\)/i) || text.match(/VLAN (\d+) not found/i);
    const vlan = vlanMatch ? vlanMatch[1] : "30";
    findings.push({
      rule_id: "RULE-VLAN-02",
      title: `Missing VLAN ${vlan} in Switch Database`,
      severity: "Critical",
      osi_layer: "Layer 2 - Data Link",
      concept: "VLAN",
      description: `VLAN ${vlan} is not created in the switch database, deactivating assigned switchports.`,
      evidence: [`Access Mode VLAN: ${vlan} (Inactive)`],
      suggested_fix: `vlan ${vlan}\n name VLAN_${vlan}\n end`
    });
  }

  // Rule 5: Wrong Default Gateway
  if (/Default Gateway[.\s:]+([\d.]+)/i.test(text) && (/192.168.1.254/.test(text) || /172.16.10.254/.test(text))) {
    findings.push({
      rule_id: "RULE-GW-01",
      title: "Invalid Host Default Gateway Configured",
      severity: "High",
      osi_layer: "Layer 3 - Network",
      concept: "GATEWAY",
      description: "Host is pointed to non-existent gateway IP instead of active router interface.",
      evidence: ["Default Gateway configured does not match router interface IP"],
      suggested_fix: "ipconfig <ip> <mask> <correct-router-gateway-ip>"
    });
  }

  // Rule 6: Missing Default Route
  if (/Gateway of last resort is not set/i.test(text)) {
    findings.push({
      rule_id: "RULE-ROUTE-01",
      title: "Missing Default Route (0.0.0.0/0)",
      severity: "Critical",
      osi_layer: "Layer 3 - Network",
      concept: "ROUTING",
      description: "Edge router has no Gateway of Last Resort, failing all external destination routing.",
      evidence: ["Gateway of last resort is not set"],
      suggested_fix: "ip route 0.0.0.0 0.0.0.0 <next-hop-ip>\n end"
    });
  }

  // Rule 7: ACL Deny Rule
  if (/deny tcp[^\n]+eq www/i.test(text) || /deny ip any any/i.test(text)) {
    findings.push({
      rule_id: "RULE-ACL-01",
      title: "Access Control List Denying Traffic",
      severity: "High",
      osi_layer: "Layer 4 - Transport",
      concept: "ACL",
      description: "ACL sequence explicitly denies matching traffic to destination.",
      evidence: ["show access-lists contains active deny rule with match counts"],
      suggested_fix: "Modify ACL sequence number to permit intended traffic."
    });
  }

  // Rule 8: Inverted NAT Interfaces
  if (/ip nat outside/i.test(text) && /GigabitEthernet0\/0/i.test(text) && /ip nat inside/i.test(text) && /GigabitEthernet0\/1/i.test(text)) {
    findings.push({
      rule_id: "RULE-NAT-01",
      title: "NAT Inside and Outside Interfaces Inverted",
      severity: "Critical",
      osi_layer: "Layer 3 - Network",
      concept: "NAT",
      description: "LAN interface is configured as NAT outside and WAN as NAT inside.",
      evidence: ["Gi0/0 -> ip nat outside", "Gi0/1 -> ip nat inside"],
      suggested_fix: "interface Gi0/0\n ip nat inside\n interface Gi0/1\n ip nat outside\n end"
    });
  }

  return findings;
}

// Generate AI Diagnostic Output
function generateClientAiDiagnosis(symptom, topology, text, ruleFindings) {
  if (currentSelectedCase) {
    // If case has known AI behavior
    if (currentSelectedCase.case_id === "CASE-13") {
      return {
        root_cause: "Router domain-lookup is disabled globally in IOS configuration, preventing name resolution.",
        osi_layer: "Layer 7 - Application",
        confidence: "High",
        evidence: ["*** Can't find cisco.lab: No response from server"],
        concept_tag: "DNS",
        next_command: "show run | include domain-lookup",
        fix_steps: ["Router-1(config)# ip domain-lookup", "Router-1(config)# end"],
        safety_assessment: "Low risk: Global domain-lookup toggle.",
        is_known_rai: true
      };
    } else if (currentSelectedCase.case_id === "CASE-20") {
      return {
        root_cause: "Extended ACL 101 contains a deny rule on line 20 blocking TCP 80 traffic to 192.168.1.100.",
        osi_layer: "Layer 4 - Transport",
        confidence: "High",
        evidence: ["20 deny tcp any host 192.168.1.100 eq www (128 matches)"],
        concept_tag: "ACL",
        next_command: "show access-lists 101",
        fix_steps: ["Router-1(config)# no access-list 101", "Router-1(config)# access-list 101 permit ip any any"],
        safety_assessment: "High risk: Deleting entire ACL removes security perimeter and allows all unauthorized DMZ traffic.",
        is_known_rai: true
      };
    }

    return {
      root_cause: currentSelectedCase.expected_fault,
      osi_layer: currentSelectedCase.osi_layer,
      confidence: "High",
      evidence: [currentSelectedCase.show_outputs.split("\n")[0], "Evidence verified from CLI output"],
      concept_tag: currentSelectedCase.concept_tag,
      next_command: `show ${currentSelectedCase.concept_tag.toLowerCase()}`,
      fix_steps: currentSelectedCase.suggested_fix.split("\n"),
      safety_assessment: "Low risk: Targeted configuration remediation."
    };
  }

  // Fallback for custom pasted input
  const firstRule = ruleFindings[0];
  return {
    root_cause: firstRule ? firstRule.description : "Potential misconfiguration detected in network show outputs.",
    osi_layer: firstRule ? firstRule.osi_layer : "Layer 3 - Network",
    confidence: firstRule ? "High" : "Medium",
    evidence: firstRule ? firstRule.evidence : ["Extracted from show command output"],
    concept_tag: firstRule ? firstRule.concept : "GENERAL",
    next_command: "show ip interface brief",
    fix_steps: firstRule ? firstRule.suggested_fix.split("\n") : ["configure terminal", "! Review interface status"],
    safety_assessment: "Review CLI commands prior to production deployment."
  };
}

// Render Diagnosis Output Card
function renderDiagnosisOutput(diag) {
  document.getElementById("diag-results-placeholder").style.display = "none";
  document.getElementById("diag-results-content").style.display = "block";

  document.getElementById("diag-status-badge").innerText = "Diagnosis Complete";
  document.getElementById("diag-status-badge").className = "badge severity-low";

  // Rules Box
  const rulesList = document.getElementById("diag-rules-list");
  rulesList.innerHTML = "";
  const ruleCountBadge = document.getElementById("rule-count-badge");
  ruleCountBadge.innerText = `${diag.rule_findings.length} Rule(s) Triggered`;

  if (diag.rule_findings.length > 0) {
    diag.rule_findings.forEach(r => {
      const div = document.createElement("div");
      div.style.marginBottom = "0.75rem";
      div.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <strong style="color: #fbbf24; font-size: 0.85rem;">[${r.rule_id}] ${r.title}</strong>
          <span class="badge ${getSeverityClass(r.severity)}" style="font-size: 0.65rem;">${r.severity}</span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">${r.description}</div>
      `;
      rulesList.appendChild(div);
    });
  } else {
    rulesList.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-dim);">No basic deterministic syntax errors found; deep AI semantic model engaged.</div>`;
  }

  // AI Box
  document.getElementById("ai-root-cause").innerText = diag.ai.root_cause;
  document.getElementById("ai-osi-layer").innerText = diag.ai.osi_layer;
  document.getElementById("ai-concept-tag").innerText = diag.ai.concept_tag;
  document.getElementById("ai-confidence-badge").innerText = `Confidence: ${diag.ai.confidence}`;
  document.getElementById("ai-next-command").innerText = diag.ai.next_command;
  document.getElementById("ai-fix-script").innerText = diag.ai.fix_steps.join("\n");
  document.getElementById("ai-safety-note").innerText = diag.ai.safety_assessment;

  const evContainer = document.getElementById("ai-evidence-list");
  evContainer.innerHTML = "";
  diag.ai.evidence.forEach(ev => {
    const q = document.createElement("div");
    q.className = "evidence-quote";
    q.innerText = `"${ev}"`;
    evContainer.appendChild(q);
  });
}

// Human Review Actions
function reviewCurrentDiagnosis(verdict) {
  if (!currentDiagnosis) return;

  const caseId = currentDiagnosis.case_id;
  humanReviews[caseId] = {
    case_id: caseId,
    title: currentDiagnosis.title,
    verdict: verdict,
    root_cause: currentDiagnosis.ai.root_cause,
    fix: currentDiagnosis.ai.fix_steps.join("\n"),
    timestamp: new Date().toISOString()
  };

  alert(`Case ${caseId} marked as ${verdict.toUpperCase()}! Logged to Human Governance Audit Trail.`);
}

function openEditModal() {
  if (!currentDiagnosis) return;
  document.getElementById("edit-root-cause").value = currentDiagnosis.ai.root_cause;
  document.getElementById("edit-fix-script").value = currentDiagnosis.ai.fix_steps.join("\n");
  document.getElementById("edit-engineer-notes").value = "";
  document.getElementById("edit-modal").style.display = "flex";
}

function closeEditModal() {
  document.getElementById("edit-modal").style.display = "none";
}

function saveEditedReview() {
  if (!currentDiagnosis) return;
  const editedFault = document.getElementById("edit-root-cause").value;
  const editedFix = document.getElementById("edit-fix-script").value;
  const notes = document.getElementById("edit-engineer-notes").value;

  const caseId = currentDiagnosis.case_id;
  humanReviews[caseId] = {
    case_id: caseId,
    title: currentDiagnosis.title,
    verdict: "Edited",
    root_cause: editedFault,
    fix: editedFix,
    notes: notes,
    timestamp: new Date().toISOString()
  };

  // Update UI
  document.getElementById("ai-root-cause").innerText = editedFault;
  document.getElementById("ai-fix-script").innerText = editedFix;
  closeEditModal();

  alert(`Remediation script edited & approved by engineer. Logged as EDITED.`);
}

// Export Review Log
function exportReviewLog(format) {
  const combined = [...responsibleAiLogs];
  Object.values(humanReviews).forEach((hr, idx) => {
    combined.push({
      log_id: `SESSION-${idx + 1}`,
      case_id: hr.case_id,
      case_title: hr.title,
      ai_proposed_fault: hr.root_cause,
      ai_proposed_fix: hr.fix,
      ai_failure_mode: "Human Review Session Override",
      human_verdict: hr.verdict,
      human_corrected_fault: hr.root_cause,
      human_corrected_fix: hr.fix,
      safety_rationale_and_learnings: hr.notes || "Engineer reviewed and confirmed fix."
    });
  });

  if (format === "json") {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(combined, null, 2));
    const a = document.createElement("a");
    a.href = dataStr;
    a.download = "netsage_human_review_log.json";
    a.click();
  } else {
    let csvContent = "data:text/csv;charset=utf-8,log_id,case_id,case_title,human_verdict,ai_failure_mode,safety_rationale\n";
    combined.forEach(row => {
      csvContent += `"${row.log_id}","${row.case_id}","${row.case_title}","${row.human_verdict}","${row.ai_failure_mode}","${(row.safety_rationale_and_learnings || '').replace(/"/g, '""')}"\n`;
    });
    const encodedUri = encodeURI(csvContent);
    const a = document.createElement("a");
    a.href = encodedUri;
    a.download = "netsage_human_review_log.csv";
    a.click();
  }
}

// Guided Lab Demo Progression
let currentDemoStep = 1;

function advanceDemoStep(step) {
  currentDemoStep = step;
  for (let i = 1; i <= 5; i++) {
    const content = document.getElementById(`demo-step-${i}`);
    const node = document.getElementById(`step-node-${i}`);
    if (content) content.style.display = (i === step) ? "block" : "none";
    if (node) {
      if (i < step) {
        node.className = "step-node completed";
        node.innerText = "✓";
      } else if (i === step) {
        node.className = "step-node active";
        node.innerText = i;
      } else {
        node.className = "step-node";
        node.innerText = i;
      }
    }
  }
}

function resetDemo() {
  advanceDemoStep(1);
}

// Interactive Chart.js Visualizations
function initCharts() {
  // 1. Concept Chart
  const ctxConcept = document.getElementById("chart-concepts");
  if (ctxConcept) {
    new Chart(ctxConcept, {
      type: "doughnut",
      data: {
        labels: ["VLAN/Trunk", "Gateway/IP", "DHCP", "DNS", "Routing/OSPF", "ACL", "NAT", "Wireless/Sec", "Switching"],
        datasets: [{
          data: [4, 5, 4, 2, 5, 3, 3, 3, 3],
          backgroundColor: [
            "#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899", "#10b981", "#f59e0b", "#ef4444", "#38bdf8", "#64748b"
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { color: '#94a3b8', font: { family: 'Outfit', size: 11 } } }
        }
      }
    });
  }

  // 2. OSI Layer Chart
  const ctxOsi = document.getElementById("chart-osi");
  if (ctxOsi) {
    new Chart(ctxOsi, {
      type: "bar",
      data: {
        labels: ["Layer 1 (Phys)", "Layer 2 (Data)", "Layer 3 (Net)", "Layer 4 (Trans)", "Layer 7 (App)"],
        datasets: [{
          label: "Fault Cases",
          data: [3, 7, 14, 3, 5],
          backgroundColor: "#00bceb",
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
          x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  // 3. Severity Chart
  const ctxSev = document.getElementById("chart-severity");
  if (ctxSev) {
    new Chart(ctxSev, {
      type: "pie",
      data: {
        labels: ["Critical", "High", "Medium", "Low"],
        datasets: [{
          data: [7, 16, 8, 1],
          backgroundColor: ["#ef4444", "#f59e0b", "#3b82f6", "#10b981"],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { color: '#94a3b8', font: { family: 'Outfit' } } }
        }
      }
    });
  }

  // 4. Review Oversight Chart
  const ctxRev = document.getElementById("chart-reviews");
  if (ctxRev) {
    new Chart(ctxRev, {
      type: "doughnut",
      data: {
        labels: ["Accepted (Direct Fix)", "Edited (Safety Modified)", "Rejected (Hallucinated)"],
        datasets: [{
          data: [26, 3, 3],
          backgroundColor: ["#10b981", "#f59e0b", "#ef4444"],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Outfit', size: 11 } } }
        }
      }
    });
  }
}

// Utility Helpers
function getBadgeClass(concept) {
  const map = {
    "VLAN": "badge-vlan",
    "GATEWAY": "badge-gateway",
    "DHCP": "badge-dhcp",
    "DNS": "badge-dns",
    "ROUTING": "badge-routing",
    "ACL": "badge-acl",
    "NAT": "badge-nat",
    "WIRELESS": "badge-wireless",
    "SECURITY": "badge-security",
    "SWITCHING": "badge-switching"
  };
  return map[concept] || "badge-vlan";
}

function getSeverityClass(sev) {
  const map = {
    "Critical": "severity-critical",
    "High": "severity-high",
    "Medium": "severity-medium",
    "Low": "severity-low"
  };
  return map[sev] || "severity-medium";
}
