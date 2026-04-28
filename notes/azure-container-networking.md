# Azure Container Networking — CNS, DNC, AZR

## Components Overview

| Component | Full Name | Runs Where |
|---|---|---|
| CNS | Container Network Service | On every AKS node (DaemonSet) |
| DNC | Distributed Network Controller | Azure managed infrastructure (outside your cluster) |
| AZR | Availability Zone Resiliency | Flag in CNS config |

---

## CNS — Container Network Service

- Runs on every node as a **DaemonSet** in `kube-system` namespace
- Responsible for assigning IP addresses to pods
- Manages the network interface on each node
- Communicates with DNC to request/release IPs
- Caches IP allocation state locally — if DNC is unreachable, existing pods keep networking

```bash
# View CNS pods once kubectl is connected
kubectl get pods -n kube-system | grep cns
kubectl describe daemonset azure-cns -n kube-system
```

---

## DNC — Distributed Network Controller

- Azure-managed service — not visible in your subscription or cluster
- Allocates IP ranges for nodes
- Coordinates IP address pools across the cluster
- Bridges CNS on your node to Azure's VNet

### Deployment Model (AKS)
- **One DNC deployment per Azure region**
- **Active-passive HA** — one replica per availability zone, only one active at a time
- All CNS nodes talk to the single active DNC
- On zone failure, passive replica in healthy zone is promoted to active

```
eastus region
┌─────────────────────────────────────────────────┐
│  Zone 1          Zone 2          Zone 3         │
│  DNC (ACTIVE)    DNC (passive)   DNC (passive)  │
│  CNS-A           CNS-B           CNS-C          │
└─────────────────────────────────────────────────┘
```

---

## AZR — Availability Zone Resiliency

- A **feature flag in CNS config** to enable zone-aware IP allocation
- When enabled, CNS communicates its zone identity to DNC
- DNC tracks IP pools per zone instead of globally

### Without AZR (disabled)
- CNS has no zone awareness
- On zone failure, IPs from dead zone returned to global pool
- Risk of IP conflicts when zone recovers — same IP assigned to two pods
- Packet routing becomes unpredictable

### With AZR (enabled)
- CNS tells DNC which zone it belongs to
- DNC holds IPs from failed zone — does not reallocate them
- New pods get IPs from correct zone pool only
- On zone recovery, failed zone's IPs cleanly handed back — no conflicts

### Example

```
Zone 1: 10.0.1.x    Zone 2: 10.0.2.x (DOWN)    Zone 3: 10.0.3.x

WITHOUT AZR:
  Zone 2 goes down → 10.0.2.x returned to global pool
  New pod on Zone 1 gets 10.0.2.4 → routing issues
  Zone 2 recovers → IP conflict

WITH AZR:
  Zone 2 goes down → DNC holds 10.0.2.x, marks zone unavailable
  New pod on Zone 1 gets 10.0.1.6 → correct, no issues
  Zone 2 recovers → cleanly reclaims 10.0.2.x pool
```

---

## AKS vs ACI — DNC Differences

| | AKS | ACI |
|---|---|---|
| DNC type | Centralized, managed by Azure | Runs as a process (PP) co-located with container group |
| DNC scope | Per region (shared across clusters) | Per container group |
| Underlying VM | Customer owned | Azure owned (shared host) |
| Isolation boundary | Customer VNet | DNC itself |
| Workload type | Long-running | Ephemeral, short-lived |

### Why ACI runs DNC as a co-located process
- ACI containers are ephemeral — calling a central DNC adds latency
- Local DNC means IP allocation has no external dependency
- Fits ACI's serverless nature — self-contained, no central service needed

---

## Full Architecture Flow

```
Pod needs an IP
      │
      ▼
azure-cns (DaemonSet on your node)
      │  requests IP from correct zone pool (if AZR enabled)
      ▼
DNC (Azure managed, active replica in healthy zone)
      │  allocates IP from your VNet subnet
      ▼
Pod gets IP from your Azure VNet
```

---

## Interview Talking Points

**On CNS/DNC:**
> "CNS runs as a DaemonSet on every node and handles IP assignment for pods. It communicates with DNC — a centralized Azure-managed service — to allocate IPs from the VNet. CNS caches state locally so if DNC is temporarily unreachable, existing pod networking isn't affected."

**On AZR:**
> "CNS has an AZR flag — Availability Zone Resiliency — that makes IP allocation zone-aware. When enabled, CNS communicates its zone identity to DNC so IP pools are managed per-zone. This matters during zone failures because you don't want IPs from a failed zone being incorrectly recycled, causing conflicts when the zone recovers."

**On DNC HA:**
> "DNC follows an active-passive HA model — one replica per availability zone but only one active at a time. This prevents split-brain IP allocation conflicts while ensuring zone-level fault tolerance. On zone failure, the passive replica in a healthy zone is promoted to active."

**On AKS vs ACI:**
> "In AKS, DNC is a centralized managed service per region. In ACI, DNC runs as a co-located process inside the container group — this makes sense because ACI workloads are ephemeral and short-lived, so local IP management avoids latency and external service dependencies."
