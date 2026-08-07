"""Centralized Loguru logging configuration."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from enterprise_fraud_detection.config.settings import Settings


def configure_logging(settings: Settings) -> None:
    """Configure console logging and a daily rotating project log file."""
    settings.paths.logs.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.logging.level,
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )
    logger.add(
        Path(settings.paths.logs) / "application_{time:YYYY-MM-DD}.log",
        level=settings.logging.level,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        enqueue=True,
        encoding="utf-8",
        backtrace=False,
        diagnose=False,
    )
