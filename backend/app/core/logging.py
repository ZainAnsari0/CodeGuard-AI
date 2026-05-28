"""
CodeGuard AI - Structured Logging Configuration
Configures structlog for JSON-formatted structured logging.
"""

import logging
import structlog


def setup_logging(debug: bool = False, log_level_name: str = None) -> None:
    """Configure structlog for structured JSON logging."""
    if log_level_name:
        log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    elif debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=log_level,
    )