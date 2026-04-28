import uuid
import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager

from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings


class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    short_url: str


redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    yield
    await redis_client.aclose()


app = FastAPI(title="URL Shortener", lifespan=lifespan)

Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/shorten", response_model=ShortenResponse)
async def shorten(body: ShortenRequest, request: Request):
    code = uuid.uuid4().hex[:8]
    await redis_client.set(code, str(body.url))
    base = str(request.base_url).rstrip("/")
    return ShortenResponse(short_url=f"{base}/{code}")


@app.get("/shorten", response_model=ShortenResponse)
async def shorten_via_query(url: HttpUrl, request: Request):
    code = uuid.uuid4().hex[:8]
    await redis_client.set(code, str(url))
    base = str(request.base_url).rstrip("/")
    return ShortenResponse(short_url=f"{base}/{code}")


@app.get("/{code}")
async def redirect(code: str):
    original_url = await redis_client.get(code)
    if not original_url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(url=original_url)
