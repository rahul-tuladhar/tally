"""Request tracing middleware."""
import logging
import time
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracing requests and responses."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()

        # Get request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_host = request.client.host if request.client else "unknown"

        # Log request
        logger.info(
            f"Request: {method} {path} from {client_host}"
            + (f" with params {query_params}" if query_params else "")
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {method} {path} completed in {duration:.2f}s "
                f"with status {response.status_code}"
            )

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"Error: {method} {path} failed after {duration:.2f}s: {str(e)}"
            )
            raise


def add_tracing_middleware(app: FastAPI) -> None:
    """Add tracing middleware to FastAPI application."""
    app.add_middleware(TracingMiddleware)
