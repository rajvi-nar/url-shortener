# Helm — Package Manager for Kubernetes

## What is Helm?

Helm is a package manager for Kubernetes — like apt for Ubuntu or pip for Python, but for K8s apps.

Instead of applying raw YAML files manually with kubectl, Helm lets you:
- Bundle all your K8s manifests into a single reusable package (a "chart")
- Parameterize values (image tag, replicas, ports) so the same chart works across environments
- Track releases, upgrade, and roll back with simple commands

---

## Chart Structure

```
helm/
  url-shortener/
    Chart.yaml          ← chart metadata (name, version, appVersion)
    values.yaml         ← all configurable defaults in one place
    templates/          ← K8s YAMLs with {{ .Values.xxx }} placeholders
      namespace.yaml
      app/
        deployment.yaml
        service.yaml
        configmap.yaml
      redis/
        deployment.yaml
        service.yaml
```

### Chart.yaml
Metadata about the chart itself.
- `version` — chart version, bump when you change the chart structure
- `appVersion` — your app's version (maps to the image tag)

### values.yaml
The single source of truth for all configurable values.
Every hardcoded value in your raw YAMLs (image, replicas, ports) moves here.
Override at deploy time with `--set` or a separate values file.

### templates/
Your K8s YAMLs with Go template syntax replacing hardcoded values:
- `{{ .Values.app.replicas }}` → pulls from values.yaml
- `{{ .Values.app.image.repository }}:{{ .Values.app.image.tag }}` → builds image string

---

## Key Commands

```bash
# Render templates locally without deploying (dry run)
helm template url-shortener ./helm/url-shortener

# Validate chart for errors
helm lint ./helm/url-shortener

# Deploy the chart
helm install url-shortener ./helm/url-shortener

# Override a value at deploy time
helm install url-shortener ./helm/url-shortener --set app.image.tag=v2

# Deploy with a separate values file (e.g. for production)
helm install url-shortener ./helm/url-shortener -f values-prod.yaml

# Update a running deployment
helm upgrade url-shortener ./helm/url-shortener

# See all deployed Helm releases
helm list

# See release history
helm history url-shortener

# Roll back to previous release
helm rollback url-shortener 1

# Delete everything the chart created
helm uninstall url-shortener
```

---

## kubectl apply vs helm install

**Why use Helm over kubectl at all?**

kubectl can do everything Helm does — you could apply every manifest manually with `kubectl apply`. Helm is just a layer on top that solves real problems at scale:

| Problem with raw kubectl | How Helm solves it |
|--------------------------|-------------------|
| You have 6 YAML files — apply them one by one | `helm install` applies all of them in one command |
| You want to change the image tag — edit the YAML directly | `helm upgrade --set app.image.tag=v2` — no manual file editing |
| You want to roll back to yesterday's config | `helm rollback url-shortener 2` — one command, done |
| You deploy to dev, staging, prod — each needs slightly different values | One chart, three `values.yaml` files |
| Someone asks "what's deployed right now?" | `helm list` shows every release, version, and timestamp |
| You want to delete the whole app cleanly | `helm uninstall` removes everything the chart created |

**In practice — same result, very different experience:**

| Without Helm | With Helm |
|---|---|
| kubectl apply -f k8s/namespace.yaml | helm install url-shortener ./helm/url-shortener |
| kubectl apply -f k8s/app/deployment.yaml | (same single command — applies all templates) |
| kubectl apply -f k8s/app/service.yaml | |
| kubectl apply -f k8s/app/configmap.yaml | |
| kubectl apply -f k8s/redis/deployment.yaml | |
| kubectl apply -f k8s/redis/service.yaml | |
| kubectl apply -f ... again to update | helm upgrade url-shortener ./helm/url-shortener |
| No history, no rollback | helm rollback url-shortener 1 |
| Manual tracking of what's deployed | helm list shows all releases |

**Short answer:** kubectl is the tool, Helm is the package manager. Like `python` vs `pip` — you don't need pip, but it makes managing things much easier at scale.

---

## How Helm Tracks Releases

Helm stores release history as **Secrets** inside the cluster (in the same namespace).
Each upgrade creates a new secret with the full state — this is how rollback works.

```bash
kubectl get secrets -n url-shortener | grep helm
# sh.helm.release.v1.url-shortener.v1
# sh.helm.release.v1.url-shortener.v2  ← after upgrade
```

---

## When to Use Helm

| Situation | Use Helm? |
|---|---|
| Learning K8s primitives hands-on | No — raw manifests teach you more |
| Deploying to multiple environments (dev/staging/prod) | Yes |
| Installing community software (Prometheus, Nginx, cert-manager) | Yes — use charts from ArtifactHub |
| CI/CD pipelines | Yes |
| Production apps | Yes |

---

## Interview Talking Points

**On what Helm is:**
> "Helm is a package manager for Kubernetes. It lets you template your manifests so the same chart can deploy to dev, staging, and production just by swapping values. It also tracks release history inside the cluster as Secrets, which enables rollbacks without any external state store."

**On helm install vs kubectl apply:**
> "kubectl apply is stateless — it just sends YAML to the API server. Helm tracks what it deployed, stores history, and lets you roll back. For production apps, Helm gives you upgrade and rollback semantics that kubectl apply doesn't."

**On values.yaml:**
> "All environment-specific config — image tags, replica counts, service types — lives in values.yaml. You can override individual values with --set at deploy time, or pass a whole environment-specific file with -f. The chart itself never changes, just the values."
