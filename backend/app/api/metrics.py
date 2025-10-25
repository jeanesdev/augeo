"""Prometheus metrics endpoint.

Exposes /metrics in the Prometheus text format. Other modules should import
metrics from `app.core.metrics` and increment counters as appropriate.
"""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter()


@router.get("/metrics", tags=["metrics"])
async def metrics_endpoint() -> Response:
    """Return Prometheus-formatted metrics for scraping.

    Returns the default registry's metrics in text format with the
    appropriate content type.
    """
    body = generate_latest()
    return Response(content=body, media_type=CONTENT_TYPE_LATEST)
