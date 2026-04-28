# Interview Questions & Answers — URL Shortener Project

Everything covered across Phases 1–5: FastAPI, Docker, Kubernetes, AKS, Terraform, Helm, Prometheus/Grafana.

---

## Python / FastAPI

**What is FastAPI and why did you choose it over Flask?**
> FastAPI is a modern Python web framework built on Starlette and Pydantic. It gives you automatic request validation, auto-generated OpenAPI docs, and native async support. Flask is synchronous by default and has no built-in validation — FastAPI is faster and requires less boilerplate for APIs.

**What is Pydantic and how does it help with validation?**
> Pydantic validates data using Python type hints. When a request comes in, FastAPI uses Pydantic models to automatically check that the body has the right fields and types. If validation fails, FastAPI returns a 422 error automatically — you don't write any validation code yourself.

**What is an async context manager and why did you use `lifespan`?**
> A lifespan function runs setup code before the app starts and teardown code after it shuts down. We used it to create the Redis connection on startup and close it cleanly on shutdown. The older `@app.on_event("startup")` decorator is deprecated — `lifespan` is the current recommended approach.

**What is a 307 redirect vs 301?**
> 301 is a permanent redirect — browsers cache it and won't hit your server again. 307 is a temporary redirect — the browser always asks your server. For a URL shortener, 307 is correct because short codes could point to different URLs in future.

---

## Docker

**Walk me through your Dockerfile. Why multi-stage?**
> We have two stages: `builder` installs all dependencies into a virtual environment, and `runtime` copies only the venv and app code into a clean image. The final image doesn't have pip, build tools, or the requirements file — only what's needed to run. This reduces image size and attack surface.

**What does `COPY --from=builder` do?**
> It copies files from a previous build stage into the current stage. We use it to copy the pre-built virtual environment from the builder stage into the runtime stage, without carrying over pip or other build-time tools.

**Why use `python:3.12-slim` instead of `python:3.12`?**
> The slim variant strips out a lot of system packages and documentation that aren't needed at runtime — significantly smaller image. The full image is ~1GB, slim is ~200MB.

**What is image layering and how does it affect build speed?**
> Each instruction in a Dockerfile creates a layer. Docker caches layers — if a layer hasn't changed, it reuses the cache instead of rebuilding. That's why we `COPY requirements.txt` and install dependencies before copying app code. Dependencies change rarely, app code changes often. This way, a code-only change doesn't reinstall all packages.

---

## Kubernetes Fundamentals

**What is a Pod? How is it different from a container?**
> A Pod is the smallest deployable unit in Kubernetes. It wraps one or more containers that share the same network namespace and storage. Containers inside a Pod can communicate via `localhost`. In practice most Pods have one container, but sidecars (like logging agents) are common.

**What is a Deployment? Why not just run pods directly?**
> A Deployment manages a ReplicaSet, which ensures a desired number of pod replicas are always running. If you run a pod directly and it crashes, it's gone. A Deployment automatically restarts it, handles rolling updates, and enables rollbacks.

**What is a Service? What problem does it solve?**
> Pods have ephemeral IPs that change on every restart. A Service gives a stable DNS name and IP that always routes to the correct pods. It uses label selectors to find pods — if a pod restarts and gets a new IP, the Service automatically picks it up.

**What is the difference between ClusterIP, NodePort, and LoadBalancer?**
> ClusterIP is internal only — only accessible within the cluster. NodePort exposes the service on a port on every node — accessible from outside but not production-ready. LoadBalancer provisions a cloud load balancer (in our case Azure) with a public IP — the standard way to expose services publicly.

**What is a ConfigMap?**
> A ConfigMap stores non-sensitive configuration as key-value pairs and injects them into pods as environment variables or files. We used it to pass the Redis URL to the app. For sensitive data like passwords, you'd use a Secret instead.

**What does `kubectl rollout restart` do?**
> It gracefully cycles all pods in a deployment one by one, following the rolling update strategy (new pod comes up before old one goes down — zero downtime). We used it to force AKS to pull the updated Docker image after we pushed a new version.

**What is etcd and what does it store?**
> etcd is the key-value database that stores all Kubernetes cluster state — every object (pods, deployments, services, secrets) is stored there. The API server reads from and writes to etcd. kubectl is stateless — it just sends requests to the API server which then reads/writes etcd.

**What does CoreDNS do?**
> CoreDNS is the DNS server inside the cluster. It lets pods resolve service names to IPs. For example, our app connects to `redis:6379` — CoreDNS resolves `redis` to the ClusterIP of the Redis service. Without it, you'd have to hardcode IPs.

---

## Kubernetes Networking

**How does port-forwarding work?**
> `kubectl port-forward` opens a tunnel through the Kubernetes API server. kubectl listens on a local port and forwards every byte to the target pod through the API server's existing authenticated connection. It doesn't open firewall holes — it piggybacks on the existing secure kubectl connection.

**How did you access Grafana without a public IP?**
> We couldn't get a fourth public IP due to Azure subscription limits. Instead we used kubectl port-forward to tunnel from the Linux machine to the Grafana pod, then used an SSH local tunnel from the laptop to the Linux machine. Chain: `laptop:3000 → SSH → linux:3000 → kubectl → grafana pod:80`.

---

## AKS / Azure

**What is AKS? What does Azure manage vs what do you manage?**
> AKS is Azure's managed Kubernetes service. Azure manages the control plane (API server, etcd, scheduler) for free. You manage the worker nodes (and pay for the VMs), your workloads, and networking configuration.

**What is ACR and how did you connect it to AKS?**
> ACR is Azure Container Registry — private Docker image storage. We connected it to AKS using a role assignment (`AcrPull`) that gives the AKS kubelet identity permission to pull images from ACR. Without this, AKS can't authenticate and pods fail with `ImagePullBackOff`.

**What is a role assignment and why did you need `AcrPull`?**
> Azure RBAC uses role assignments to grant identities permission to perform actions on resources. AKS uses a managed identity to pull images — we assigned it the `AcrPull` role on the ACR resource so it has exactly the permission it needs and nothing more.

---

## Terraform

**What is Terraform and what problem does it solve?**
> Terraform is an infrastructure-as-code tool that lets you define cloud resources in `.tf` files and provision them with a single command. It solves the problem of manual, error-prone clicking in cloud consoles — your infrastructure is version-controlled, reproducible, and can be destroyed and recreated exactly.

**What is the difference between `terraform plan` and `terraform apply`?**
> `plan` shows what Terraform will do without actually doing it — like a dry run. `apply` executes the changes. Always run `plan` first to verify there are no surprises.

**What is state in Terraform?**
> Terraform keeps a `terraform.tfstate` file that maps your config to real cloud resources. It uses this to calculate what needs to change on the next apply. If you delete a resource manually in Azure without telling Terraform, the state gets out of sync — this is called state drift.

**What is idempotency?**
> Running the same Terraform apply multiple times produces the same result — if nothing changed in your config, nothing changes in the infrastructure. This is safe to run repeatedly unlike shell scripts that might create duplicate resources.

---

## Helm

**What is Helm?**
> Helm is the package manager for Kubernetes. Like pip for Python, it lets you install, upgrade, and uninstall Kubernetes applications as versioned packages called charts. It templates your YAML so the same chart can deploy to dev, staging, and prod with different values.

**How does Helm store release history?**
> Helm stores each release revision as a Kubernetes Secret in the cluster namespace. After three upgrades you'd see `sh.helm.release.v1.url-shortener.v1`, `.v2`, `.v3`. This is how rollback works — Helm reads the previous secret and re-applies it.

**When do you use `helm upgrade` vs `kubectl rollout restart`?**
> `helm upgrade` when you changed Helm chart files or values — it applies the new manifests. `kubectl rollout restart` when only the Docker image changed but the chart config didn't — it just cycles the pods to pull the new image.

---

## Prometheus & Grafana

**What is Prometheus and how does it collect metrics?**
> Prometheus is a pull-based monitoring system. Every 15 seconds it scrapes a `/metrics` HTTP endpoint on each target and stores the numbers in a time-series database. This is different from push-based systems where apps send metrics to a central collector.

**What is a ServiceMonitor?**
> A ServiceMonitor is a custom Kubernetes resource (added by the prometheus-operator) that tells Prometheus which services to scrape, on which port, at which path, and how often. Without it, Prometheus doesn't know your app exists. It's the glue between Prometheus and your app.

**Why did the ServiceMonitor not work initially?**
> The ServiceMonitor's selector looked for services with the label `app: url-shortener`, but our service template had no labels on the metadata — only on the spec selector. Adding `labels: app: url-shortener` to the service metadata fixed it.

**What are the 4 golden signals?**
> Defined by Google's SRE book — the four most important things to monitor:
> - **Latency** — how long requests take
> - **Traffic** — how many requests per second
> - **Errors** — what percentage of requests fail
> - **Saturation** — how full the system is (CPU, memory)

**What is `rate()` and why do you need it for counters?**
> Counters only go up — the raw value tells you total requests since the app started, which isn't useful for a graph. `rate()` calculates the per-second change over a time window, giving you velocity (requests/sec) instead of total count.

**What is the difference between counter and gauge?**
> A counter only increases (total requests, total errors). A gauge goes up and down (current memory usage, active connections). You use `rate()` on counters. You use gauges directly.

**What is kube-state-metrics vs node-exporter?**
> node-exporter runs on each node and collects hardware metrics — CPU, memory, disk, network. kube-state-metrics watches the Kubernetes API and exposes object state — how many pods are running, deployment replica counts, pod restarts. They answer different questions: node-exporter = "how is the machine doing?", kube-state-metrics = "how is Kubernetes doing?"

---

## General DevOps / Architecture

**What is the difference between ACI and AKS?**
> ACI is serverless containers — you give it an image, it runs it, you don't manage any nodes. AKS is a full Kubernetes cluster where you manage worker nodes and orchestration. ACI is for short-lived burst workloads, AKS is for long-running production apps needing scheduling, scaling, and service discovery.

**How is ACI multitenant?**
> ACI uses Hyper-V isolation — each container gets its own lightweight VM with its own Linux kernel. Multiple customers' containers can run on the same physical host but cannot see each other's memory or processes. This is stronger than standard Docker where containers share the host kernel.

**What is LCOW?**
> Linux Containers on Windows. Using Hyper-V, a minimal Linux VM (LinuxKit) runs underneath each Linux container on a Windows host. In ACI you just specify `osType: Linux` — Azure handles the LCOW layer transparently.

---

## Behavioural / Project walkthrough

**Walk me through this project from scratch.**
> "I built a URL shortener as a hands-on DevOps learning project. Starting with a FastAPI + Redis app locally, I containerized it with a multi-stage Dockerfile and pushed to GHCR. Then I deployed it to a local kind cluster to learn all the Kubernetes primitives — pods, deployments, services, configmaps. After that I provisioned an AKS cluster on Azure using Terraform, pushed the image to ACR, and deployed using raw kubectl manifests. I then converted everything to a Helm chart for templating and release management. Finally I added observability — installed kube-prometheus-stack via Helm, added a `/metrics` endpoint to the FastAPI app using prometheus-fastapi-instrumentator, and created a ServiceMonitor so Prometheus auto-scrapes the app. I monitored the four golden signals in Grafana."

**Why did Prometheus not scrape your app initially?**
> "The ServiceMonitor had a selector looking for services labeled `app: url-shortener`, but our Helm service template had no labels in the metadata section — only in the spec selector. Prometheus couldn't match the ServiceMonitor to any service. I diagnosed it by port-forwarding to Prometheus and checking its targets API, then fixed it by adding the label to the service metadata."

**What would you do differently for production?**
> "Use proper secrets management (Azure Key Vault or Kubernetes Secrets for Redis passwords), add persistent storage for Redis (data is lost on pod restart), set up proper Ingress with TLS instead of LoadBalancer per service, add horizontal pod autoscaling, set up CI/CD with GitHub Actions to automate builds and deploys, and use Terraform remote state in Azure Blob Storage instead of local state."
