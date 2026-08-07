"""Reusable dataset download, loading, and validation utilities."""

from __future__ import annotations

import json
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd
from loguru import logger

from enterprise_fraud_detection.config.settings import Settings


@dataclass(frozen=True)
class ValidationReport:
    """Serializable summary of dataset quality checks."""

    rows: int
    columns: int
    column_names: list[str]
    target_column: str
    target_present: bool
    missing_values: dict[str, int]
    duplicate_rows: int
    dtypes: dict[str, str]
    statistics: dict[str, dict[str, float | int | None]]


class DatasetManager:
    """Manage the Phase 1 raw Credit Card Fraud Detection dataset."""

    def __init__(self, settings: Settings) -> None:
        """Initialize dataset operations with centralized application settings."""
        self.settings = settings
        self.raw_directory = settings.paths.raw_data
        self.dataset_path = self.raw_directory / settings.dataset.filename

    def download(self, force: bool = False) -> Path:
        """Download and extract the dataset into the configured raw directory."""
        self.raw_directory.mkdir(parents=True, exist_ok=True)
        if self.dataset_path.exists() and not force:
            logger.info("Dataset already exists at {}", self.dataset_path)
            return self.dataset_path
        if not self.settings.dataset.download_url:
            raise ValueError("No dataset URL configured. Set DATASET_URL or dataset.download_url.")

        archive_path = self.raw_directory / "creditcardfraud.zip"
        request = Request(
            self.settings.dataset.download_url,
            headers={"User-Agent": "fraud-detection-phase1"},
        )
        logger.info("Downloading dataset from {}", self.settings.dataset.download_url)
        with urlopen(request, timeout=120) as response, archive_path.open("wb") as archive_file:
            archive_file.write(response.read())
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(self.raw_directory)
        archive_path.unlink(missing_ok=True)
        if not self.dataset_path.exists():
            csv_files = list(self.raw_directory.glob("*.csv"))
            if len(csv_files) == 1:
                csv_files[0].replace(self.dataset_path)
            else:
                raise FileNotFoundError(f"Expected {self.dataset_path} after extraction")
        logger.info("Dataset available at {}", self.dataset_path)
        return self.dataset_path

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """Load the raw CSV dataset, raising a clear error when absent."""
        dataset_path = path or self.dataset_path
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found at {dataset_path}. Run download first.")
        return pd.read_csv(dataset_path)

    def validate(self, data: pd.DataFrame | None = None) -> ValidationReport:
        """Run structural and basic statistical checks and save a JSON report."""
        frame = data if data is not None else self.load()
        numeric_statistics: dict[str, dict[str, float | int | None]] = {}
        for column in frame.select_dtypes(include="number").columns:
            description = frame[column].describe()
            numeric_statistics[column] = {
                key: (None if pd.isna(value) else float(value))
                for key, value in description.to_dict().items()
            }
        report = ValidationReport(
            rows=int(frame.shape[0]),
            columns=int(frame.shape[1]),
            column_names=[str(column) for column in frame.columns],
            target_column=self.settings.dataset.target_column,
            target_present=self.settings.dataset.target_column in frame.columns,
            missing_values={str(key): int(value) for key, value in frame.isna().sum().items()},
            duplicate_rows=int(frame.duplicated().sum()),
            dtypes={str(key): str(value) for key, value in frame.dtypes.items()},
            statistics=numeric_statistics,
        )
        self.settings.paths.reports.mkdir(parents=True, exist_ok=True)
        report_path = self.settings.paths.reports / "dataset_validation.json"
        report_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        logger.info("Dataset validation report written to {}", report_path)
        return report
