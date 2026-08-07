"""Benchmark model and prediction service latency."""

from __future__ import annotations

import json
import statistics
import time
from datetime import UTC, datetime

import pandas as pd

from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.serving.prediction import PredictionService
from enterprise_fraud_detection.utils.logging import configure_logging

if __name__ == "__main__":
    settings = get_settings()
    configure_logging(settings)
    target = settings.dataset.target_column
    frame = pd.read_csv(settings.paths.raw_data / settings.dataset.filename, nrows=100).drop(
        columns=[target]
    )
    service = PredictionService(settings)
    single_times = []
    for _, row in frame.head(10).iterrows():
        started = time.perf_counter()
        service.predict_one(row.to_dict(), input_reference="benchmark")
        single_times.append((time.perf_counter() - started) * 1000)
    batch_times = []
    for _ in range(3):
        started = time.perf_counter()
        service.predict_batch(frame, input_reference="benchmark")
        batch_times.append((time.perf_counter() - started) * 1000)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "rows_per_batch": len(frame),
        "single_prediction_latency_ms": {
            "mean": statistics.mean(single_times),
            "p95": sorted(single_times)[max(0, int(len(single_times) * 0.95) - 1)],
        },
        "batch_prediction_latency_ms": {
            "mean": statistics.mean(batch_times),
            "p95": sorted(batch_times)[max(0, int(len(batch_times) * 0.95) - 1)],
        },
    }
    output = settings.production.benchmark_output_directory
    output.mkdir(parents=True, exist_ok=True)
    (output / "prediction_benchmark.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
