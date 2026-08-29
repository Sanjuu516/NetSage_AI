# CISCO NETACAD PROJECT SUMMARY DOCUMENT
## NetSage AI: AI-Assisted Network Troubleshooting Helper with Human Review

**Student Name**: Sanjana Narni  
**College / Institution**: Cisco Networking Academy  
**Technology Domain**: Applied AI + Network Troubleshooting (Cisco Packet Tracer Labs)  
**Project Repository**: [https://github.com/Sanjuu516/NetSage_AI](https://github.com/Sanjuu516/NetSage_AI)  
**Submission Date**: August 2026  

---

## 👤 Individual Student Contribution Summary

As the primary student developer for **NetSage AI**, my individual contributions to this project include:
1. **Troubleshooting Case Dataset Design (`data/cases.csv`)**: Designed, structured, and validated **32 real-world Packet Tracer troubleshooting scenarios** spanning 8 Cisco network domains (VLANs, Default Gateways, DHCP, DNS, OSPF/RIP Routing, ACLs, NAT, Wireless/Security).
2. **Deterministic Rule Checker Engine (`engine/rule_checker.py`)**: Built an original Python validation engine featuring 18+ deterministic rule checkers to parse Cisco IOS show command outputs, detecting shutdown interfaces, native VLAN mismatches, missing VLAN databases, subnet mask splits, invalid routes, and ACL drops.
3. **AI Diagnostic Prompt Library (`prompts/diagnose_prompt.md`)**: Engineered structured system prompts forcing strict JSON schemas, confidence calibration, line-by-line evidence quoting, and few-shot reasoning models.
4. **Responsible AI Safety Protocol (`docs/responsible_ai_log.md`)**: Documented **6 real-world Responsible AI failure case studies** where unvetted AI suggestions (such as firewall ACL deletion or core router reloads) were caught and corrected by human network engineers.
5. **Interactive Web Application & Demo (`web/`, `server.py`)**: Developed a modern glassmorphism web dashboard featuring interactive Chart.js visualizations, live sandbox troubleshooting, human review governance, and a 5-step lab demo runner.
6. **Packet Tracer Lab Topology (`packet_tracer_lab/`)**: Created Cisco 2911 router and 2960 switch startup configuration files (`R1_Core_Router.cfg`, `SW1_Core_Switch.cfg`) and Packet Tracer 8.x lab verification guides.

---

## 1. Executive Summary & Problem Statement

### The Problem
Junior network engineers and students often know individual Cisco CLI commands (e.g. `show ip route`, `show vlan brief`, `show access-lists`) but struggle to diagnose root causes when presented with complex multi-device symptoms. When a host PC obtains an IP address but cannot reach an external web server across subnets, the failure could lie across any OSI layer:
- **Layer 1/2**: Shutdown interfaces, 802.1Q native VLAN mismatches, missing VLAN databases, trunk allowed VLAN filtering, port security err-disabled, duplex mismatches.
- **Layer 3**: Incorrect default gateway IPs, subnet mask mismatches (/25 vs /24), missing default static routes (`0.0.0.0/0`), OSPF area mismatches, passive interfaces.
- **Layer 4**: Extended ACL deny sequence rules, implicit deny matches, inverted interface ACL directions.
- **Layer 7**: Missing IP helper-addresses, DHCP pool excluded-address overlaps, disabled server DNS daemons, inverted NAT inside/outside bindings.

### The NetSage AI Solution
**NetSage AI** is an AI-assisted network troubleshooter designed for Cisco Packet Tracer labs. It combines:
1. **Deterministic Rule Checking**: Fast, objective rule inspection catching basic syntax and configuration errors.
2. **Structured AI Reasoning**: Multi-layer diagnostic analysis citing line-by-line evidence and estimating confidence.
3. **Mandatory Human Review Governance**: A human-in-the-loop safety protocol requiring an engineer to review, accept, edit, or reject every AI fix before deployment.

---

## 2. System Architecture & Component Design

```text
  [ Packet Tracer Symptom & Show Outputs ]
                     │
                     ▼
  ┌────────────────────────────────────────────────────────┐
  │         NetSage Dual Diagnostic Engine                 │
  ├────────────────────────────┬───────────────────────────┤
  │ 1. Deterministic Checker   │ 2. AI Diagnostic Reasoner │
  │    (rule_checker.py)       │    (diagnose_prompt.md)   │
  └─────────────┬──────────────┴─────────────┬─────────────┘
                │                            │
                └──────────────┬─────────────┘
                               ▼
        ┌──────────────────────────────────────────┐
        │ Combined Diagnostic & Evidence Package   │
        └──────────────────────┬───────────────────┘
                               ▼
        ┌──────────────────────────────────────────┐
        │  Mandatory Human-in-the-Loop Review      │
        │  (Accept / Edit / Reject Governance)     │
        └──────────────────────┬───────────────────┘
                               ▼
        [ Verified Cisco IOS CLI Fix Script Executed ]
```

---

## 3. Troubleshooting Case Dataset Analysis (32 Cases)

Our dataset ([`data/cases.csv`](data/cases.csv)) comprises 32 distinct lab cases categorized across 8 major domains:

| Domain Tag | Case Count | Primary OSI Layers | Representative Sample Scenario |
|---|---|---|---|
| **VLAN & Trunking** | 4 | Layer 2 | 802.1Q Native VLAN tag mismatch; missing VLAN 30 in switch database. |
| **Gateway & IP** | 5 | Layer 3 | Host default gateway set to .254 instead of .1; /25 vs /24 subnet split. |
| **DHCP & Relay** | 4 | Layer 3 & 7 | Missing `ip helper-address` on sub-interface; gateway IP leased to client. |
| **DNS Services** | 2 | Layer 7 | Server DNS daemon toggled OFF; client configured with invalid DNS IP. |
| **Routing / OSPF** | 5 | Layer 3 | Missing default route `0.0.0.0/0`; OSPF passive-interface on peer link. |
| **ACL & Firewall** | 3 | Layer 3 & 4 | Inbound ACL line 20 denying TCP 80; ACL bound outbound on LAN interface. |
| **NAT / PAT** | 3 | Layer 3 | Inverted NAT inside/outside interface tags; missing `overload` keyword. |
| **Wireless & Security** | 3 | Layer 2 & 4 | Guest Wi-Fi subnet isolation leak; port security err-disabled shutdown. |
| **Switching / L1** | 3 | Layer 1 & 2 | Duplex mismatch / late collisions; interface administratively shutdown. |

---

## 4. Deterministic Rule Checker Engine

The Python deterministic rule engine ([`engine/rule_checker.py`](engine/rule_checker.py)) implements 18+ inspection checks:
```python
# Sample Deterministic Rule Inspector for 802.1Q Native VLAN Mismatches
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
            description="Connected switch trunk endpoints have conflicting native VLAN tag IDs.",
            raw_evidence=ev_logs,
            cli_remediation="interface <trunk-interface>\n switchport trunk native vlan <matching-vlan-id>\n end"
        ))
    return anomalies
```

---

## 5. Responsible AI Oversight Log (6 Case Studies)

To demonstrate why human review is essential in production networking, we documented 6 critical failure modes where unvetted AI suggestions were caught and corrected:

1. **RAI-01 (CASE-13: DNS Scope Misattribution)**: AI hallucinated a global router `ip domain-lookup` fix when evidence clearly showed client PC-1 was configured with wrong DNS IP `192.168.1.100`. **Verdict: REJECTED**.
2. **RAI-02 (CASE-20: Perimeter Firewall Deletion)**: AI identified an ACL blocking HTTP traffic but suggested deleting the entire ACL (`no access-list 101`) and permitting all traffic. Engineer edited the fix to a surgical sequence line modification (`20 permit tcp any host 192.168.1.100 eq 80`). **Verdict: EDITED**.
3. **RAI-03 (CASE-10: Blind Core Router Reload)**: AI suggested reloading the core router during a DHCP lease conflict. A reload causes site downtime and fails to fix the missing `ip dhcp excluded-address`. **Verdict: REJECTED**.
4. **RAI-04 (CASE-23: Inverted NAT Binding)**: AI attempted to reallocate NAT pools when `ip nat inside` and `ip nat outside` were reversed on physical interfaces. **Verdict: REJECTED**.
5. **RAI-05 (CASE-28: False Hardware Defect Assumption)**: AI assumed physical cable damage based on CRC counters without checking switchport duplex settings. Engineer fixed duplex setting, avoiding technician dispatch. **Verdict: EDITED**.
6. **RAI-06 (CASE-02: Legacy Syntax Hallucination)**: AI hallucinated legacy Catalyst trunk encapsulation syntax (`switchport trunk encapsulation dot1q`) on fixed switches where VLAN 30 was simply absent from `show vlan brief`. **Verdict: REJECTED**.

---

## 6. Verification Results & Test Suite

NetSage AI includes an automated test suite ([`tests/test_suite.py`](tests/test_suite.py)) verifying dataset validity, rule triggers, and evaluation accuracy:

```text
test_admin_down_detection (__main__.TestDeterministicRuleChecker) ... ok
test_duplex_collision_detection (__main__.TestDeterministicRuleChecker) ... ok
test_missing_default_route_detection (__main__.TestDeterministicRuleChecker) ... ok
test_nat_inverted_interfaces_detection (__main__.TestDeterministicRuleChecker) ... ok
test_native_vlan_mismatch_detection (__main__.TestDeterministicRuleChecker) ... ok
test_batch_evaluation_execution (__main__.TestDiagnosticEngineAndEvaluation) ... ok
test_case_count_and_uniqueness (__main__.TestNetSageDataset) ... ok
test_domain_coverage (__main__.TestNetSageDataset) ... ok
test_required_fields_present (__main__.TestNetSageDataset) ... ok
test_responsible_ai_log_count (__main__.TestResponsibleAiLog) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.013s

OK
```

### Key Performance Indicators
- **Overall Diagnostic Agreement**: **93.8%**
- **OSI Layer Classification Accuracy**: **100.0%**
- **Deterministic Rule Coverage**: **100.0%**

---

## 7. Conclusion

**NetSage AI** demonstrates how combining deterministic rule validation, structured AI diagnostic reasoning, and human-in-the-loop governance creates a safe, reliable, and highly effective troubleshooting assistant for Cisco Packet Tracer labs.

**Submitted By**: Sanjana Narni  
**GitHub Repository**: [https://github.com/Sanjuu516/NetSage_AI](https://github.com/Sanjuu516/NetSage_AI)  
