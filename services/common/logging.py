"""Structured logging configuration for VoiceGoat."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from services.common.config import settings


def add_service_context(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add service context to all log entries."""
    event_dict["service"] = event_dict.get("service", "voicegoat")
    event_dict["environment"] = settings.environment.value
    return event_dict


def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_service_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.debug:
        # Development: pretty console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            min_level=logging.DEBUG if settings.debug else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(service: str | None = None) -> structlog.BoundLogger:
    """Get a logger instance with optional service context."""
    logger = structlog.get_logger()
    if service:
        logger = logger.bind(service=service)
    return logger


# Configure logging on import
configure_logging()
