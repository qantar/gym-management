from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 2)
        response.headers["X-Process-Time"] = str(duration)
        return response
