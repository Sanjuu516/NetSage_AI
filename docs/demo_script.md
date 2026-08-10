# NetSage AI: 5-to-10 Minute Demonstration Script & Video Guide

## Demo Presentation Overview
* **Project Name**: NetSage AI - Applied AI Network Troubleshooting Helper with Human Review
* **Target Duration**: 6 - 8 Minutes
* **Presenters**: Network Engineering & Applied AI Team (2-3 students)
* **Goal**: Demonstrate how NetSage AI ingests Packet Tracer symptoms and Cisco `show` command outputs, leverages a dual-engine architecture (deterministic rules + structured AI reasoner) to suggest root causes and remediation scripts, and enforces a mandatory **Human-in-the-Loop Review** to catch dangerous AI hallucinations before deployment.

---

## Timed Turn-by-Turn Script

### [00:00 - 01:15] Section 1: Problem Statement & NetSage AI Overview
* **Visual**: Open NetSage AI Dashboard (`http://localhost:8080`).
* **Speaker 1**:
  > "Hello everyone. Today we are presenting **NetSage AI**, an intelligent troubleshooting companion for Cisco and Packet Tracer networking labs.
  > 
  > Junior network engineers often know individual CLI commands like `show ip route` or `show vlan brief`, but struggle to connect high-level symptoms to root causes. When a PC gets an IP but can't reach a server, is it VLAN tagging, a wrong default gateway, DHCP relay, an ACL, or NAT?
  >
  > Furthermore, blindly letting an AI apply network configuration fixes is dangerous—an AI might delete an entire firewall ACL or reboot a core router. NetSage AI solves this through a dual-engine architecture:
  > 1. A **Deterministic Python Rule Checker** that catches objective syntax and configuration bugs.
  > 2. A **Structured AI Diagnostic Reasoner** that cites line-by-line evidence and assigns confidence.
  > 3. A **Mandatory Human Review Governance Layer** where engineers inspect, accept, edit, or reject every diagnosis."

---

### [01:15 - 02:45] Section 2: Case Dataset & Dashboard Analytics
* **Visual**: Show KPI cards and dynamic Chart.js charts on the Dashboard tab, then switch to the **Case Explorer** tab.
* **Speaker 2**:
  > "Let's review our dataset and dashboard metrics.
  > 
  > We built a dataset of **32 comprehensive troubleshooting cases** derived from realistic Packet Tracer scenarios covering 8 major domains:
  > - **VLAN & 802.1Q Trunking** (native VLAN mismatches, missing VLAN databases, trunk allowed filters)
  > - **Gateway & Subnetting** (wrong default gateway, /25 vs /24 mask mismatches, shutdown SVIs)
  > - **DHCP & Relay** (missing IP helper-addresses, excluded-address overlap, DHCP snooping untrusted ports)
  > - **DNS Services** (disabled server daemons, misconfigured client DNS IPs)
  > - **Routing & OSPF** (missing default routes, passive interfaces, area mismatches, MTU mismatches)
  > - **ACLs & Firewalls** (port 80 deny rules, implicit deny matches, inverted direction filters)
  > - **NAT / PAT** (inside/outside interface inversion, missing overload keyword, missing subnet ACLs)
  > - **Wireless & Layer 2 Security** (guest Wi-Fi isolation leaks, port security err-disabled)
  >
  > As shown on the charts, our deterministic rule checker covers 100% of standard syntax flaws, while our AI reasoner achieves a 93.8% calibrated agreement rate with ground truth."

---

### [02:45 - 04:15] Section 3: Live Interactive Diagnostic Sandbox
* **Visual**: Switch to **Live Diagnosis** tab. Click **Load Preset Case** (e.g. `CASE-03: 802.1Q Native VLAN Mismatch on Trunk`).
* **Speaker 1**:
  > "Let's test the live interactive diagnostic engine in real time.
  > 
  > Here we have two switches experiencing intermittent packet loss and CDP syslog warnings.
  > When we click **Run NetSage AI Diagnosis**, our system simultaneously runs:
  > - **Deterministic Rules**: Instantly identifies `RULE-VLAN-01: 802.1Q Trunk Native VLAN Mismatch`, noting Switch-A is Native VLAN 10 while Switch-B is Native VLAN 1.
  > - **AI Diagnostic Reasoner**: Synthesizes the root cause, cites the exact quoted lines from `show interfaces trunk`, assigns `Layer 2 - Data Link`, recommends the next verification command (`show interfaces trunk`), and generates the exact copyable Cisco IOS remediation:
  >   `Switch-B(config)# interface GigabitEthernet0/1`
  >   `Switch-B(config-if)# switchport trunk native vlan 10`"

---

### [04:15 - 06:30] Section 4: The Broken Lab Demo & Responsible AI Safety Catch
* **Visual**: Switch to **Guided Lab Demo** tab (or **Human Review Log** tab).
* **Speaker 3**:
  > "Now let's walk through our flagship live lab scenario: **The DMZ Perimeter ACL Outage**.
  > 
  > **Step 1 (The Broken State)**: External users cannot access DMZ Web Server `192.168.1.100:80`. Ping works, but HTTP times out.
  > 
  > **Step 2 (The AI Diagnosis)**: NetSage AI accurately identifies that Extended ACL 101 line 20 has `deny tcp any host 192.168.1.100 eq www (128 matches)`.
  > However, look at what the raw AI model proposed as a fix:
  > `Router-1(config)# no access-list 101`
  > `Router-1(config)# access-list 101 permit ip any any`
  > 
  > **Step 3 (The Human Review Safety Catch)**: If an automated script executed this raw AI fix, it would delete the entire firewall and expose the internal DMZ to the open Internet!
  > 
  > As the human network engineer, I intervene on the workbench:
  > I click **Edit / Modify Fix** and change the action to a surgical named ACL sequence fix:
  > `Router-1(config)# ip access-list extended 101`
  > `Router-1(config-ext-nacl)# no 20`
  > `Router-1(config-ext-nacl)# 20 permit tcp any host 192.168.1.100 eq 80`
  > `Router-1(config-ext-nacl)# end`
  > 
  > **Step 4 (Applying Fix)**: We commit the verified commands to Router-1.
  > 
  > **Step 5 (Verification)**: We run our simulated `curl http://192.168.1.100` test. It returns `HTTP/1.1 200 OK` with 0% packet loss, while the firewall perimeter remains completely secure!"

---

### [06:30 - 07:30] Section 5: Responsible AI Governance Log & Conclusion
* **Visual**: Switch to **Human Review Log** tab and show the export buttons (Export CSV / Export JSON).
* **Speaker 2**:
  > "In our Responsible AI log, we have documented **6 critical real-world failure modes** where raw AI needed human correction:
  > 1. Hallucinating router domain-lookup for a client DNS misconfiguration.
  > 2. Proposing total ACL deletion.
  > 3. Blindly suggesting a core router reload during DHCP conflicts.
  > 4. Missing inverted NAT inside/outside interface designations.
  > 5. Assuming physical cable defect during duplex mismatches.
  > 6. Hallucinating legacy Catalyst trunk encapsulation commands.
  > 
  > All logs can be exported directly to JSON or CSV for corporate Change Advisory Board (CAB) auditing.
  > 
  > In conclusion, NetSage AI combines the speed of rule-based checkers and the reasoning of modern AI with the indispensable safety of human oversight. Thank you!"

---

## Equipment & Setup Checklist
- [x] Web Server running (`/usr/bin/python3 server.py 8080`)
- [x] Browser window loaded on `http://localhost:8080`
- [x] Screen recording software (OBS / QuickTime) active at 1080p
- [x] Audio input configured and tested
