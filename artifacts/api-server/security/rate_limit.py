import time
import logging
from collections import defaultdict
from threading import Lock
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, requests_per_minute: int = 100):
        self.rate = requests_per_minute
        self.clients: defaultdict[str, list[float]] = defaultdict(list)
        self.lock = Lock()

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        with self.lock:
            # Filter requests in the last 60 seconds
            self.clients[client_ip] = [
                t for t in self.clients[client_ip] if now - t < 60
            ]

            if len(self.clients[client_ip]) < self.rate:
                self.clients[client_ip].append(now)
                return True
            return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)

    async def dispatch(self, request: Request, call_next):
        # Allow requests to documentation or health endpoints without hard limits
        if request.url.path in [
            "/api/healthz",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
        ]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        if not self.limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for client IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
            )

        return await call_next(request)
