# Cluster Pods — What's Running and Why

## All pods across namespaces

```
NAMESPACE       POD                                           ROLE
kube-system     azure-cns                                     Networking
kube-system     azure-ip-masq-agent                          Networking
kube-system     cloud-node-manager                           Node management
kube-system     coredns (x2)                                 DNS
kube-system     coredns-autoscaler                           DNS scaling
kube-system     csi-azuredisk-node                           Storage
kube-system     csi-azurefile-node                           Storage
kube-system     konnectivity-agent (x2)                      Control plane tunnel
kube-system     konnectivity-agent-autoscaler                Tunnel scaling
kube-system     kube-proxy                                    Network routing
kube-system     metrics-server (x2)                          Resource metrics
monitoring      alertmanager                                  Alerts
monitoring      grafana                                       Dashboards
monitoring      kube-state-metrics                           K8s object metrics
monitoring      prometheus-operator                          ServiceMonitor watcher
monitoring      prometheus-node-exporter                     Node metrics
monitoring      prometheus                                    Metrics scraper + store
url-shortener   redis                                        URL store
url-shortener   url-shortener                                FastAPI app
```

---

## `kube-system` — Kubernetes internals (AKS managed)

| Pod | Role |
|-----|------|
| `azure-cns` | Azure Container Networking Service — assigns IP addresses to pods |
| `azure-ip-masq-agent` | Handles IP masquerading so pods can reach the internet |
| `cloud-node-manager` | Tells Kubernetes about the Azure VM underneath (node labels, capacity) |
| `coredns` (x2) | DNS server for the cluster — how pods resolve `redis` → `10.0.x.x` by name. Two copies for high availability |
| `coredns-autoscaler` | Automatically adds more CoreDNS pods if cluster grows |
| `csi-azuredisk-node` | Driver for mounting Azure Disk storage into pods (like a USB drive for pods) |
| `csi-azurefile-node` | Same but for Azure File shares (shared network storage) |
| `konnectivity-agent` (x2) | Secure tunnel between the AKS control plane and your nodes. Two copies for HA |
| `konnectivity-agent-autoscaler` | Scales konnectivity agents as cluster grows |
| `kube-proxy` | Runs on every node — handles network routing rules so Services work |
| `metrics-server` (x2) | Collects CPU/memory from pods — powers `kubectl top pods` |

---

## `monitoring` — Prometheus stack (installed via Helm)

| Pod | Role |
|-----|------|
| `alertmanager` | Receives alerts from Prometheus, routes them (email, Slack, etc.) |
| `grafana` | Dashboard UI — visualize all metrics in the browser |
| `kube-state-metrics` | Watches K8s objects (deployments, pods) and exposes their state as metrics |
| `prometheus-operator` | Watches for ServiceMonitor objects and configures Prometheus automatically |
| `prometheus-node-exporter` | Runs on every node, collects node-level metrics (CPU, memory, disk) |
| `prometheus` | The core — scrapes all targets and stores metrics |

---

## `url-shortener` — Your app

| Pod | Role |
|-----|------|
| `redis` | In-memory store — maps short codes to original URLs |
| `url-shortener` | FastAPI app — handles `/shorten` and redirect requests |

---

## The big picture

```
Your app pods        → emit metrics at /metrics
prometheus           → scrapes /metrics every 15s
kube-state-metrics   → scrapes K8s object state
node-exporter        → scrapes node CPU/memory
grafana              → visualizes everything
alertmanager         → fires alerts if things go wrong
kube-proxy + coredns → make networking work for all of the above
```

---

## Useful commands

```bash
# See all pods across all namespaces
kubectl get pods -A

# See pods in a specific namespace
kubectl get pods -n monitoring
kubectl get pods -n url-shortener
kubectl get pods -n kube-system

# See CPU and memory usage per pod
kubectl top pods -A

# Describe a pod (events, volumes, env vars)
kubectl describe pod <pod-name> -n <namespace>

# View logs of a pod
kubectl logs <pod-name> -n <namespace>
```
