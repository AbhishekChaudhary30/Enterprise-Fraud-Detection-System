"""Thread-safe application metrics with JSON persistence."""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class MetricsSnapshot:
    """Aggregated runtime counters and latency statistics."""

    started_at: str
    request_count: int = 0
    error_count: int = 0
    prediction_count: int = 0
    batch_prediction_count: int = 0
    total_prediction_rows: int = 0
    total_latency_ms: float = 0.0
    last_latency_ms: float = 0.0
    last_status_code: int = 0

    @property
    def average_latency_ms(self) -> float:
        """Return mean request latency when requests exist."""
        return self.total_latency_ms / self.request_count if self.request_count else 0.0


class MetricsRegistry:
    """Collect process-local API and prediction metrics safely across requests."""

    def __init__(self, output_path: Path) -> None:
        """Initialize a registry and its persistence target."""
        self.output_path = output_path
        self._lock = threading.RLock()
        self._snapshot = MetricsSnapshot(started_at=datetime.now(UTC).isoformat())

    def observe_request(self, latency_ms: float, status_code: int) -> None:
        """Record one HTTP request."""
        with self._lock:
            self._snapshot.request_count += 1
            self._snapshot.total_latency_ms += latency_ms
            self._snapshot.last_latency_ms = latency_ms
            self._snapshot.last_status_code = status_code
            if status_code >= 500:
                self._snapshot.error_count += 1
            self._persist()

    def observe_prediction(self, rows: int = 1, batch: bool = False) -> None:
        """Record single or batch prediction volume."""
        with self._lock:
            self._snapshot.prediction_count += 1
            self._snapshot.total_prediction_rows += rows
            if batch:
                self._snapshot.batch_prediction_count += 1
            self._persist()

    def snapshot(self) -> dict[str, Any]:
        """Return application, process, CPU, and memory metrics."""
        with self._lock:
            payload = asdict(self._snapshot)
            payload["average_latency_ms"] = self._snapshot.average_latency_ms
        payload.update(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "process_id": os.getpid(),
                "memory_rss_bytes": _memory_rss(),
                "cpu_time_seconds": time.process_time(),
            }
        )
        return payload

    def _persist(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(json.dumps(self.snapshot(), indent=2), encoding="utf-8")


def _memory_rss() -> int:
    """Return resident memory bytes using psutil when available, otherwise zero."""
    try:
        import psutil

        return int(psutil.Process(os.getpid()).memory_info().rss)
    except ImportError:
        return 0
