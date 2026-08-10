# NetSage AI: Technical Lab Demo Walkthrough

## Scenario Summary
* **Lab Name**: Broken Perimeter ACL & Inter-VLAN Routing Lab
* **Target Devices**: Cisco 2911 Router (`Router-1`), Cisco 2960 Switch (`Switch-1`), DMZ Web Server (`192.168.1.100`), External Client (`203.0.113.10`)
* **Core Objective**: Diagnose why HTTP web traffic to DMZ fails while ICMP ping succeeds, catch AI over-remediation, apply surgical Cisco IOS commands, and verify full service restoration.

---

## 1. Initial State (The Broken Lab)

### Observable Symptoms
```text
External-Client> ping 192.168.1.100
Pinging 192.168.1.100 with 32 bytes of data:
Reply from 192.168.1.100: bytes=32 time=14ms TTL=127
Reply from 192.168.1.100: bytes=32 time=13ms TTL=127
Ping statistics: Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)

External-Client> curl -I http://192.168.1.100
curl: (7) Failed to connect to 192.168.1.100 port 80: Connection timed out
```

### Cisco IOS Show Output Inspection
```text
Router-1# show ip interface GigabitEthernet0/1
GigabitEthernet0/1 is up, line protocol is up
  Internet address is 203.0.113.2/30
  Inbound access list is 101
  Outbound access list is not set

Router-1# show access-lists 101
Extended IP access list 101
    10 permit icmp any any (45 matches)
    20 deny tcp any host 192.168.1.100 eq www (128 matches)
    30 permit ip any any
```

---

## 2. NetSage AI Diagnostic Output

### Deterministic Rule Checker Finding
```json
{
  "rule_id": "RULE-ACL-01",
  "title": "Access List Deny Rule Dropping Traffic",
  "severity": "High",
  "osi_layer": "Layer 4 - Transport",
  "concept": "ACL",
  "description": "ACL contains an active deny entry matching traffic: '20 deny tcp any host 192.168.1.100 eq www (128 matches)'",
  "evidence": ["20 deny tcp any host 192.168.1.100 eq www (128 matches)"]
}
```

### Raw AI Reasoner Output (Simulated Unvetted Generation)
```json
{
  "root_cause": "Extended ACL 101 on Router-1 line 20 explicitly denies TCP port 80 (HTTP) traffic to web server 192.168.1.100 while permitting ICMP.",
  "osi_layer": "Layer 4 - Transport",
  "confidence": "High",
  "evidence": ["20 deny tcp any host 192.168.1.100 eq www (128 matches)"],
  "concept_tag": "ACL",
  "next_command": "show access-lists 101",
  "fix_steps": [
    "Router-1(config)# no access-list 101",
    "Router-1(config)# access-list 101 permit ip any any"
  ],
  "safety_assessment": "High risk: Deleting entire ACL removes security perimeter and allows all unauthorized DMZ traffic."
}
```

---

## 3. Human-in-the-Loop Review Intervention

* **Engineer Verdict**: **EDITED**
* **Safety Hazard Identified**: The raw AI suggested deleting the entire ACL (`no access-list 101`) and permitting all IP traffic. In a production enterprise network or DMZ, deleting an ACL destroys the firewall perimeter, exposing internal management ports (SSH/Telnet/SNMP) and backend database servers to unrestricted external exploitation.
* **Human Corrected Configuration**:
  Instead of deleting the entire ACL, use Cisco IOS Named Extended ACL sequence editing:
  ```text
  Router-1(config)# ip access-list extended 101
  Router-1(config-ext-nacl)# no 20
  Router-1(config-ext-nacl)# 20 permit tcp any host 192.168.1.100 eq 80
  Router-1(config-ext-nacl)# end
  ```

---

## 4. Execution & Verification

### Configuration Application
```text
Router-1# configure terminal
Enter configuration commands, one per line.  End with CNTL/Z.
Router-1(config)# ip access-list extended 101
Router-1(config-ext-nacl)# no 20
Router-1(config-ext-nacl)# 20 permit tcp any host 192.168.1.100 eq 80
Router-1(config-ext-nacl)# end
Router-1# write memory
Building configuration...
[OK]
```

### Post-Fix Show Command Validation
```text
Router-1# show access-lists 101
Extended IP access list 101
    10 permit icmp any any (45 matches)
    20 permit tcp any host 192.168.1.100 eq www (32 matches)
    30 permit ip any any
```

### End-to-End Client Reachability Validation
```text
External-Client> curl -i http://192.168.1.100
HTTP/1.1 200 OK
Date: Mon, 10 Aug 2026 12:00:00 GMT
Server: Apache/2.4.52 (Cisco-DMZ)
Content-Type: text/html; charset=UTF-8
Content-Length: 58

<html><body><h1>NetSage AI Lab Service Restored</h1></body></html>
```

### Result
- **Fault Resolved**: HTTP web traffic successfully reaches DMZ Web Server.
- **Perimeter Maintained**: Enterprise firewall rules remain intact without unvetted wildcard permissions.
- **Downtime**: 0 seconds.
