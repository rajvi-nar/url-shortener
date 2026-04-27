# URL Shortener

A URL shortening service built with FastAPI and Redis, progressively deployed from local development to Kubernetes on Azure.

## Tech Stack

- **App:** Python 3.12, FastAPI, Redis
- **Container:** Docker (multi-stage build)
- **Registry:** GitHub Container Registry (GHCR)
- **Orchestration:** Kubernetes (kind locally, AKS on Azure)

## Project Structure

```
.
├── app/
│   ├── main.py          # FastAPI routes
│   └── config.py        # Settings via environment variables
├── k8s/
│   ├── namespace.yaml
│   ├── app/
│   │   ├── configmap.yaml
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── redis/
│       ├── deployment.yaml
│       └── service.yaml
├── Dockerfile
└── requirements.txt
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/shorten` | Shorten a URL (JSON body) |
| GET | `/shorten?url=` | Shorten a URL (query param) |
| GET | `/{code}` | Redirect to original URL |

### Example

```bash
# Shorten a URL
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://kubernetes.io/docs"}'

# Response
{"short_url": "http://localhost:8000/fa3b72fe"}

# Redirect
curl -L http://localhost:8000/fa3b72fe
```

## Running Locally

**Prerequisites:** Python 3.12, Redis running on `localhost:6379`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Running with Docker

```bash
# Create network
docker network create url-shortener-net

# Start Redis
docker run -d --name redis --network url-shortener-net redis:7-alpine

# Build and run app
docker build -t url-shortener:v1 .
docker run -d \
  --name url-shortener \
  --network url-shortener-net \
  -p 8000:8000 \
  -e REDIS_URL=redis://redis:6379 \
  -e BASE_URL=http://localhost:8000 \
  url-shortener:v1
```

## Running on Kubernetes (kind)

```bash
# Create cluster
kind create cluster --name url-shortener

# Load image into kind
kind load docker-image url-shortener:v1 --name url-shortener

# Deploy
kubectl apply -R -f k8s/

# Access
kubectl port-forward -n url-shortener service/url-shortener 8000:8000
```

## Docker Image

```
ghcr.io/rajvi-nar/url-shortener:v1
```
