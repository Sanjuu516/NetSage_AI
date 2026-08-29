# NetSage AI: Cisco Packet Tracer Lab Topology & Setup Guide

**Author**: Sanjana Narni  
**Technology**: Applied AI + Network Troubleshooting (Cisco NetAcad)  
**Target Platform**: Cisco Packet Tracer 8.0+ / 8.2+

---

## 📐 Lab Topology Overview

The **NetSage AI Packet Tracer Lab** models a standard multi-vlan corporate branch connected to an ISP gateway and DMZ server farm. It is specifically designed to simulate the 32 troubleshooting cases evaluated by NetSage AI.

```text
                                [ Internet Server ]
                                  (8.8.8.8)
                                     |
                              [ ISP Router ]
                            (203.0.113.1/30)
                                     |
                          Gi0/1 (203.0.113.2/30)
                           [ Router-1 (2911) ]
                        /          |          \
            Gi0/0.10,20,40       Gi0/2         Console
                 |                 |              |
      [ Switch-1 (2960) ]   [ DMZ Server ]   [ Admin PC ]
       /     |        \     (192.168.1.100)
    Fa0/1  Fa0/2    Gi0/2
     |       |        |
  [PC-A]   [PC-B] [Switch-2]
(VLAN 10) (VLAN 20)   |
                    Fa0/5
                      |
                   [PC-C]
                 (VLAN 30)
```

---

## 🛠️ Step-by-Step Packet Tracer Setup Instructions

### 1. Device Selection & Cable Setup
1. **Routers**: Add 1 x `Cisco 2911 ISR Router` named `Router-1`.
2. **Switches**: Add 2 x `Cisco 2960 24-TT Switches` named `Switch-1` and `Switch-2`.
3. **End Devices**:
   - Add `PC-A` (Sales Department) on `Switch-1` port `Fa0/1`.
   - Add `PC-B` (Marketing Department) on `Switch-1` port `Fa0/2`.
   - Add `PC-C` (Engineering Department) on `Switch-2` port `Fa0/5`.
   - Add `DMZ-Web-Server` on `Router-1` port `Gi0/2`.
   - Add `ISP-Gateway` on `Router-1` port `Gi0/1`.

### 2. Loading Configurations in Packet Tracer
To load the configurations into Packet Tracer:
1. Double-click `Router-1` -> Go to **CLI** tab.
2. Enter global configuration mode (`enable` -> `configure terminal`).
3. Paste the contents of [`R1_Core_Router.cfg`](R1_Core_Router.cfg).
4. Double-click `Switch-1` -> Go to **CLI** tab -> Paste [`SW1_Core_Switch.cfg`](SW1_Core_Switch.cfg).

---

## 🧪 Verification Commands in Packet Tracer

### 1. Test Gateway & Subnet Reachability
From `PC-A` Command Prompt:
```cmd
PC-A> ping 192.168.10.1
PC-A> ping 192.168.20.1
```

### 2. Verify Extended Firewall ACL (Case 20 Verification)
```cmd
PC-A> curl http://192.168.1.100
```
*Expected Output*: `HTTP/1.1 200 OK - Welcome to Cisco DMZ`

### 3. Verify Deterministic Rule Inspection
Run the NetSage Python validator against Packet Tracer show outputs:
```bash
python3 engine/rule_checker.py --all
```
