import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        response: Response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        response.headers["X-Process-Time-ms"] = str(round(duration, 2))
        return response
