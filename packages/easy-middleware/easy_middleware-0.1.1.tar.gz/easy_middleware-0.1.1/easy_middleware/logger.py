import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("easy_middleware")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

class LoggerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, log_request_body: bool = False, log_response_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        # Log request
        body = None
        if self.log_request_body:
            body = await request.body()
        logger.info(
            f"Incoming request: {request.method} {request.url.path} "
            f"client={request.client.host if request.client else 'unknown'} "
            f"body={body.decode() if body else ''}"
        )

        # Process request
        response: Response = await call_next(request)

        # Log response
        duration = (time.time() - start_time) * 1000
        resp_body = None
        if self.log_response_body and hasattr(response, "body_iterator"):
            # read and reconstruct response body
            resp_body = b"".join([chunk async for chunk in response.body_iterator])
            response.body_iterator = iter([resp_body])
        logger.info(
            f"Completed response: status={response.status_code} "
            f"time={duration:.2f}ms "
            f"body={resp_body.decode() if resp_body else ''}"
        )

        return response
