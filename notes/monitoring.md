# Monitoring Setup — Prometheus + Grafana on AKS

## Goal

Observe the URL shortener running in AKS — request counts, response times, error rates — using Prometheus (metrics collection) and Grafana (dashboards).

---

## Workflow Overview

1. Add the Prometheus Helm repo
2. Install `kube-prometheus-stack` into a `monitoring` namespace
3. Add `/metrics` endpoint to the FastAPI app
4. Create a `ServiceMonitor` so Prometheus scrapes the app
5. View dashboards in Grafana

---

## Step 1 — Add Helm repo

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

Registers the Prometheus community chart registry with Helm. Only needs to be done once.

---

## Step 2 — Install kube-prometheus-stack

```bash
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.service.type=LoadBalancer \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

**What each flag does:**

| Flag | Why |
|------|-----|
| `--namespace monitoring` | Keeps monitoring stack separate from the app namespace |
| `--create-namespace` | Creates the `monitoring` namespace if it doesn't exist |
| `grafana.service.type=LoadBalancer` | Gives Grafana a public IP so you can open it in a browser |
| `serviceMonitorSelectorNilUsesHelmValues=false` | Lets Prometheus scrape ServiceMonitors from any namespace, not just its own Helm release |

**What this installs:**
- **Prometheus** — scrapes and stores metrics
- **Grafana** — dashboard UI
- **Alertmanager** — handles alerts
- **node-exporter** — collects node-level (CPU, memory, disk) metrics
- **kube-state-metrics** — collects Kubernetes object metrics (pod counts, deployments, etc.)

**Verify pods are running:**
```bash
kubectl --namespace monitoring get pods
```

**Get Grafana external IP:**
```bash
kubectl --namespace monitoring get svc kube-prometheus-stack-grafana
```

**Get Grafana admin password:**
```bash
kubectl --namespace monitoring get secrets kube-prometheus-stack-grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d && echo
```

Login: `admin` / `<password from above>`

---

## Step 3 — Add `/metrics` to FastAPI app

Install the instrumentator library:
```bash
pip install prometheus-fastapi-instrumentator
```

Add to `app/main.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

**What this one line does:**

It's a chain of three things:

- **`Instrumentator()`** — creates the instrumentator. Sets up collectors for: HTTP request count, request duration (latency), request size, and response size — all broken down by method, path, and status code.
- **`.instrument(app)`** — hooks into FastAPI middleware so every request/response is automatically measured. No changes needed to existing route handlers.
- **`.expose(app)`** — adds a `GET /metrics` route to the app. Prometheus calls this URL every 15 seconds to collect the numbers.

**Example of what `/metrics` returns:**
```
http_requests_total{method="POST",handler="/shorten",status="200"} 42
http_request_duration_seconds_bucket{handler="/shorten",le="0.1"} 40
http_request_duration_seconds_bucket{handler="/shorten",le="0.5"} 42
```

So after hitting `/shorten` 42 times, Prometheus knows: 42 total requests, 40 completed in under 100ms, all 42 in under 500ms.

Rebuild and push the Docker image, then redeploy via Helm.

---

## Step 4 — Create a ServiceMonitor

A `ServiceMonitor` is a Kubernetes custom resource (from prometheus-operator) that tells Prometheus which services to scrape and at what path.

Create `helm/url-shortener/templates/app/servicemonitor.yaml`:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: url-shortener
  namespace: {{ .Values.namespace }}
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: url-shortener
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

Apply via Helm upgrade:
```bash
helm upgrade url-shortener ./helm/url-shortener
```

---

## Step 5 — View in Grafana

1. Open `http://<grafana-external-ip>` in a browser
2. Login with `admin` / `<password>`
3. Go to **Dashboards** — pre-built dashboards for nodes, pods, and the cluster are already there
4. To see app metrics: **Explore → Metrics → search `http_requests_total`**

---

## Namespace layout

| Namespace | What's in it |
|-----------|-------------|
| `url-shortener` | FastAPI app + Redis |
| `monitoring` | Prometheus + Grafana + Alertmanager |

---

## Useful commands

```bash
# Check all monitoring pods
kubectl get pods -n monitoring

# Check Grafana service / external IP
kubectl get svc -n monitoring kube-prometheus-stack-grafana

# Check ServiceMonitor is registered
kubectl get servicemonitor -n url-shortener

# Check Prometheus targets (port-forward Prometheus UI)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
# then open http://localhost:9090/targets
```
