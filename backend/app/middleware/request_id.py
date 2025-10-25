"""Request ID middleware for distributed tracing."""

import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)

# Context variable to store request ID
request_id_context: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_context.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to all requests.

    - Generates a unique request ID for each request
    - Adds request ID to response headers
    - Stores request ID in context for logging
    - Accepts request ID from client if provided in X-Request-ID header
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and add request ID."""
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Store in context for logging
        request_id_context.set(request_id)

        # Add request ID to request state for access in routes
        request.state.request_id = request_id

        # Log request with ID
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                },
            )

            return response

        except Exception as e:
            # Log error with request ID
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise
