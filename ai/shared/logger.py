"""Structured logging system for Startup Igniter AI subsystem."""

import logging
import re
import sys
from typing import Any, Dict, Optional

try:
    import structlog  # type: ignore
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False


# Regular expressions for masking sensitive API keys in logs
SENSITIVE_PATTERNS = [
    re.compile(r"gsk_[A-Za-z0-9_]+"),               # Groq API Key
    re.compile(r"tvly-[A-Za-z0-9_-]+"),            # Tavily API Key
    re.compile(r"sbp_[A-Za-z0-9_]+"),               # Supabase Token
    re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"), # JWTs
]


def mask_sensitive_data(message: str) -> str:
    """Mask any API keys or tokens present in string output."""
    masked = message
    for pattern in SENSITIVE_PATTERNS:
        masked = pattern.sub("[REDACTED_SECRET]", masked)
    return masked


class SensitiveDataFilter(logging.Filter):
    """Logging filter to automatically redact secrets from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: mask_sensitive_data(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


def setup_ai_logger(
    log_level: str = "INFO",
    service_name: str = "startup_os_ai",
) -> logging.Logger:
    """Configure and return a structured logger for the AI subsystem.

    Args:
        log_level: Logging level string ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        service_name: Name of the service component for log tagging.

    Returns:
        Configured Logger instance.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger(service_name)
    logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    return logger


# Global logger instance for AI module
ai_logger = setup_ai_logger()


def get_ai_logger(
    context: Optional[Dict[str, Any]] = None,
) -> Any:
    """Retrieve logger instance with contextual details attached.

    Args:
        context: Context dictionary (e.g. {'project_id': '...', 'phase': 'idea'})

    Returns:
        Logger instance.
    """
    if context and HAS_STRUCTLOG:
        return structlog.get_logger("startup_os_ai").bind(**context)
    return ai_logger
