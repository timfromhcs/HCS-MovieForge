"""Structured JSON telemetry logging for workers, jobs, and system events."""

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from packages.contracts.src.worker import WorkerTelemetry


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "telemetry") and isinstance(record.telemetry, (dict, WorkerTelemetry)):
            tel = record.telemetry
            if isinstance(tel, WorkerTelemetry):
                tel = tel.model_dump()
            log_obj["telemetry"] = tel
        if hasattr(record, "job_id"):
            log_obj["job_id"] = record.job_id
        if hasattr(record, "project_id"):
            log_obj["project_id"] = record.project_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logger(name: str, log_file: Path | str | None = None, level: int = logging.INFO) -> logging.Logger:
    """Configures a structured JSON logger emitting to stdout and optionally a log file."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JsonFormatter())
        logger.addHandler(console_handler)

        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
            file_handler.setFormatter(JsonFormatter())
            logger.addHandler(file_handler)

    return logger
