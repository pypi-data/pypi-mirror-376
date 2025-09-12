import uuid
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, header_name: str = "X-Request-ID", log: bool = True):
        super().__init__(app)
        self.header_name = header_name
        self.log = log

    async def dispatch(self, request: Request, call_next: Callable):
        correlation_id = request.headers.get(self.header_name, str(uuid.uuid4()))
        start_time = time.time()
        response: Response = await call_next(request)
        response.headers[self.header_name] = correlation_id

        if self.log:
            duration = (time.time() - start_time) * 1000
            print(f"[{correlation_id}] {request.method} {request.url.path} "
                  f"status={response.status_code} time={duration:.2f}ms")

        return response
