import time
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    A sliding window rate limiting middleware that restricts requests per client IP.
    Default limit is 40 requests per minute.
    Stale IP entries are evicted every 1000 requests to prevent unbounded memory growth.
    """
    def __init__(self, app, requests_per_minute: int = 40):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        # Maps client_ip -> list of request timestamps
        self.ip_tracker = {}
        self._request_count = 0

    async def dispatch(self, request: Request, call_next) -> Response:
        # Exclude static/health check endpoints from rate limiting
        path = request.url.path
        if path == "/" or path == "/health" or path.startswith("/api/v1/infrastructure/download"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown-ip"
        current_time = time.time()

        # Clean up older timestamps for this IP
        if client_ip in self.ip_tracker:
            self.ip_tracker[client_ip] = [
                t for t in self.ip_tracker[client_ip]
                if current_time - t < 60
            ]
        else:
            self.ip_tracker[client_ip] = []

        # Periodically evict IPs with no recent activity to prevent memory leak
        self._request_count += 1
        if self._request_count % 1000 == 0:
            stale_cutoff = current_time - 600  # 10 minutes idle
            stale_ips = [
                ip for ip, timestamps in self.ip_tracker.items()
                if not timestamps or max(timestamps) < stale_cutoff
            ]
            for ip in stale_ips:
                del self.ip_tracker[ip]

        # Check limit
        if len(self.ip_tracker[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please wait a moment before trying again."
                }
            )

        # Track current request
        self.ip_tracker[client_ip].append(current_time)
        return await call_next(request)
