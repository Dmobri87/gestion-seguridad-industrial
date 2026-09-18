"""
Request logging middleware.

Responsibilities:
- Generate a unique request_id (UUID4) for every incoming HTTP request.
- Store the request_id in a context variable so any logger in the call
  chain can include it automatically (via RequestIdFilter).
- Log method, path, status_code, duration_ms and client_ip for each request.
- Skip logging for the /health endpoint to reduce noise.
- Attach the request_id as an ``X-Request-ID`` response header for tracing.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import request_id_ctx

logger = logging.getLogger("api")

# Paths that should NOT be logged (high-frequency / health-check noise)
_SKIP_PATHS: set[str] = {"/health"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that logs every HTTP request with timing and a unique ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # --- Generate and store request_id ---
        rid = uuid.uuid4().hex
        token = request_id_ctx.set(rid)

        start = time.perf_counter()
        status_code = 500  # default in case of unhandled exception

        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            # Attach header so clients / load balancers can correlate
            response.headers["X-Request-ID"] = rid
            return response
        except Exception:
            # Re-raise after logging; the exception handlers in main.py
            # will produce the actual HTTP response.
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            # Determine the real client IP (respect X-Forwarded-For behind proxy)
            client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            if not client_ip and request.client:
                client_ip = request.client.host

            path = request.url.path

            if path not in _SKIP_PATHS:
                logger.info(
                    "%s %s -> %s  (%.2f ms)  client=%s  rid=%s",
                    request.method,
                    path,
                    status_code,
                    duration_ms,
                    client_ip or "-",
                    rid,
                )

            # Reset the context variable to avoid leaking across requests
            request_id_ctx.reset(token)
