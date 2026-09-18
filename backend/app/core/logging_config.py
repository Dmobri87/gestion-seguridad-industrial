"""
Production-grade logging configuration.

Provides:
- JSON structured logging for production environments
- Pretty console logging for development
- Rotating file handlers with configurable size limits
- Separate named loggers for app, auth, database, api
- Context-aware request_id injection via a custom filter
"""

import json
import logging
import logging.handlers
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

from app.core.config import DEBUG

# ---------------------------------------------------------------------------
# Context variable: holds the current request_id (set by middleware)
# ---------------------------------------------------------------------------
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------
# Docker mounts /app/logs; local development falls back to ./logs
_DOCKER_LOG_DIR = "/app/logs"
_LOCAL_LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "logs",
)
LOG_DIR = _DOCKER_LOG_DIR if os.path.isdir("/app") else _LOCAL_LOG_DIR
os.makedirs(LOG_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_BYTES = 10 * 1024 * 1024  # 10 MB per log file
BACKUP_COUNT = 5
LOG_LEVEL = logging.DEBUG if DEBUG else logging.WARNING
LOGGER_NAMES = ("app", "auth", "database", "api")


# ===================================================================
# Custom filter that injects request_id into every LogRecord
# ===================================================================
class RequestIdFilter(logging.Filter):
    """Attach the current request_id (or '-') to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"  # type: ignore[attr-defined]
        return True


# ===================================================================
# JSON formatter  (production)
# ===================================================================
class JSONFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


# ===================================================================
# Pretty console formatter  (development)
# ===================================================================
class PrettyFormatter(logging.Formatter):
    """Human-readable coloured output for local development."""

    COLORS = {
        "DEBUG": "\033[36m",     # cyan
        "INFO": "\033[32m",      # green
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[1;31m",  # bold red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        req_id = getattr(record, "request_id", "-")
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        base = (
            f"{color}{ts} [{record.levelname:<8}]{self.RESET} "
            f"{record.name} [rid={req_id}] {record.getMessage()}"
        )
        if record.exc_info and record.exc_info[1] is not None:
            base += "\n" + self.formatException(record.exc_info)
        return base


# ===================================================================
# Public helpers
# ===================================================================

def _make_rotating_handler(filename: str) -> logging.handlers.RotatingFileHandler:
    """Create a RotatingFileHandler inside LOG_DIR."""
    path = os.path.join(LOG_DIR, filename)
    handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RequestIdFilter())
    return handler


def setup_logging() -> None:
    """
    Configure the root logger and all application loggers.

    Call this once at application startup **before** any request is processed.
    """

    # --- root logger -------------------------------------------------------
    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    # Remove any pre-existing handlers (e.g. from basicConfig)
    root.handlers.clear()

    # Console handler -------------------------------------------------------
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(LOG_LEVEL)
    if DEBUG:
        console.setFormatter(PrettyFormatter())
    else:
        console.setFormatter(JSONFormatter())
    console.addFilter(RequestIdFilter())
    root.addHandler(console)

    # Rotating file handler (always JSON, regardless of environment) ---------
    root.addHandler(_make_rotating_handler("app.log"))

    # --- named loggers -----------------------------------------------------
    for name in LOGGER_NAMES:
        named_logger = logging.getLogger(name)
        named_logger.setLevel(LOG_LEVEL)
        named_logger.addHandler(_make_rotating_handler(f"{name}.log"))
        # Propagation stays True so records also reach root (console + app.log)

    # Quiet noisy third-party loggers in production
    if not DEBUG:
        for noisy in ("uvicorn.access", "uvicorn.error", "sqlalchemy.engine"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("app").info(
        "Logging configured  |  level=%s  |  log_dir=%s  |  json=%s",
        logging.getLevelName(LOG_LEVEL),
        LOG_DIR,
        not DEBUG,
    )
