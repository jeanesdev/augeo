"""Middleware for collecting HTTP request metrics.

Tracks request count, latency, and status codes for Prometheus monitoring.
"""

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import HTTP_REQUESTS_TOTAL


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics for Prometheus."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and collect metrics.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response from downstream handlers
        """
        # Start timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Extract path without query params and truncate long paths
        path = request.url.path
        if len(path) > 100:
            path = path[:97] + "..."

        # Increment request counter
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=path,
            status=response.status_code,
        ).inc()

        # Add duration header for debugging (optional)
        response.headers["X-Process-Time"] = f"{duration:.4f}"

        return response
