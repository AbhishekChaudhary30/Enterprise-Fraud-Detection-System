"""Professional exploratory data analysis report generation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from loguru import logger

from enterprise_fraud_detection.config.settings import Settings
from enterprise_fraud_detection.data.dataset import DatasetManager

sns.set_theme(style="whitegrid", context="notebook")


def _save_figure(path: Path) -> None:
    """Save a figure with consistent output settings."""
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()


def generate_eda_report(settings: Settings, data: pd.DataFrame | None = None) -> Path:
    """Generate Phase 1 EDA figures and a Markdown summary report."""
    manager = DatasetManager(settings)
    frame = data if data is not None else manager.load()
    validation = manager.validate(frame)
    figure_directory = settings.paths.figures
    figure_directory.mkdir(parents=True, exist_ok=True)
    target = settings.dataset.target_column

    class_distribution = figure_directory / "class_distribution.png"
    plt.figure(figsize=(7, 5))
    if target in frame.columns:
        sns.countplot(data=frame, x=target)
        plt.title("Class Distribution")
        plt.xlabel(target)
        plt.ylabel("Transaction count")
    _save_figure(class_distribution)

    missing_values = frame.isna().sum().sort_values(ascending=False)
    missing_report = figure_directory / "missing_values.png"
    plt.figure(figsize=(10, 5))
    non_zero_missing = missing_values[missing_values > 0]
    if non_zero_missing.empty:
        plt.text(0.5, 0.5, "No missing values detected", ha="center", va="center")
        plt.axis("off")
    else:
        sns.barplot(x=non_zero_missing.index, y=non_zero_missing.values, color="#c45b3c")
        plt.xticks(rotation=75, ha="right")
        plt.ylabel("Missing values")
        plt.title("Missing Value Report")
    _save_figure(missing_report)

    numeric = frame.select_dtypes(include="number")
    correlation_path = figure_directory / "correlation_heatmap.png"
    plt.figure(figsize=(14, 11))
    sns.heatmap(numeric.corr(), cmap="vlag", center=0, linewidths=0.1)
    plt.title("Numeric Feature Correlation Heatmap")
    _save_figure(correlation_path)

    distribution_path = figure_directory / "feature_distributions.png"
    selected_features = [column for column in numeric.columns if column != target][:12]
    if selected_features:
        numeric[selected_features].hist(figsize=(14, 12), bins=30, color="#2f6f73")
        plt.suptitle("Feature Distributions", y=1.02)
        plt.tight_layout()
        plt.savefig(distribution_path, dpi=160, bbox_inches="tight")
        plt.close("all")

    comparison_path = figure_directory / "fraud_vs_normal.png"
    if target in frame.columns and selected_features:
        comparison_data = frame.groupby(target)[selected_features].median().T
        comparison_data.plot(kind="bar", figsize=(14, 7), color=["#2f6f73", "#c45b3c"])
        plt.title("Median Feature Values: Normal vs Fraud")
        plt.xlabel("Feature")
        plt.ylabel("Median value")
        plt.xticks(rotation=75, ha="right")
        plt.legend(title=target)
        _save_figure(comparison_path)

    summary_path = settings.paths.reports / "eda_report.md"
    settings.paths.reports.mkdir(parents=True, exist_ok=True)
    target_counts = frame[target].value_counts().to_dict() if target in frame.columns else {}
    summary = (
        f"# Exploratory Data Analysis Report\n\n"
        f"## Dataset Overview\n\n"
        f"- Rows: {validation.rows:,}\n"
        f"- Columns: {validation.columns:,}\n"
        f"- Target column: `{target}`\n"
        f"- Duplicate rows: {validation.duplicate_rows:,}\n"
        f"- Missing cells: {sum(validation.missing_values.values()):,}\n\n"
        f"## Class Distribution\n\n"
        f"```text\n{target_counts}\n```\n\n"
        f"## Generated Figures\n\n"
        f"Figures are saved in `{figure_directory.relative_to(settings.project_root)}`.\n"
    )
    summary_path.write_text(summary, encoding="utf-8")
    logger.info("EDA report written to {}", summary_path)
    return summary_path
