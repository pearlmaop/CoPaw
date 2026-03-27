import time
import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)


@contextmanager
def trace_span(name: str, metadata: Optional[dict] = None):
    """Simple tracing span context manager."""
    start = time.monotonic()
    logger.debug(f"[TRACE] Starting span: {name}")
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        logger.debug(f"[TRACE] Completed span: {name} in {elapsed:.3f}s")
