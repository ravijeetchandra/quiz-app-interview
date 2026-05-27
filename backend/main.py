import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import init_db
from routers import auth, quiz, results
import time
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", force=True)


# In-memory rate limiter (use Redis for production)
rate_limit_store = defaultdict(list)


async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.method in ("POST", "PUT", "DELETE"):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60
        max_requests = 20

        rate_limit_store[client_ip] = [
            t for t in rate_limit_store[client_ip] if now - t < window
        ]

        if len(rate_limit_store[client_ip]) >= max_requests:
            raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")

        rate_limit_store[client_ip].append(now)

    return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Quiz Interview Prep API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.middleware("http")(rate_limit_middleware)

app.include_router(auth.router)
app.include_router(quiz.router)
app.include_router(results.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/domains")
async def get_domains():
    return {"domains": settings.domain_list}
