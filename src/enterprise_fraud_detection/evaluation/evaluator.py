"""Evaluation, threshold optimization, reporting, and experiment tracking."""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from loguru import logger
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from enterprise_fraud_detection.config.settings import Settings


@dataclass(frozen=True)
class EvaluationResult:
    """Locations and key results from one evaluation run."""

    version: str
    selected_model: str
    threshold: float
    metrics_path: Path
    evaluation_report: Path
    model_card: Path
    shap_directory: Path
    experiment_history: Path


class ModelEvaluator:
    """Evaluate the latest persisted Phase 2 pipeline on its deterministic holdout."""

    def __init__(self, settings: Settings) -> None:
        """Initialize evaluation with centralized settings."""
        self.settings = settings

    def evaluate(self, frame: pd.DataFrame) -> EvaluationResult:
        """Generate metrics, plots, SHAP outputs, reports, and experiment history."""
        started = time.perf_counter()
        version = self._latest_version()
        model_directory = self.settings.paths.models / version
        pipeline = joblib.load(model_directory / "pipeline.joblib")
        metadata = json.loads((model_directory / "metadata.json").read_text(encoding="utf-8"))
        X_test, y_test = self._holdout(frame)
        probabilities = pipeline.predict_proba(X_test)[:, 1]
        threshold = self._optimize_threshold(y_test, probabilities)
        predictions = (probabilities >= threshold).astype(int)
        metrics = self._metrics(y_test, predictions, probabilities)
        logger.info("Evaluation started for {}", version)

        output = self.settings.evaluation.output_directory
        plots = self.settings.evaluation.plots_directory
        output.mkdir(parents=True, exist_ok=True)
        plots.mkdir(parents=True, exist_ok=True)
        self._write_metrics(metrics, output / "metrics.json", output / "metrics.csv")
        self._write_threshold_report(y_test, probabilities, output / "threshold_report.csv")
        self._write_error_analysis(X_test, y_test, probabilities, predictions, output)
        self._write_feature_importance(pipeline, X_test, plots, output)
        self._write_plots(y_test, probabilities, predictions, plots)
        shap_directory = self._write_shap(pipeline, X_test, plots)
        evaluation_report = self._write_evaluation_report(
            version, metadata, metrics, threshold, output / "evaluation_report.md"
        )
        model_card = self._write_model_card(
            version,
            metadata,
            metrics,
            output / "model_card.md",
            self.settings.dataset.filename,
        )
        experiment_history = self._track_experiment(
            version, metadata, metrics, threshold, time.perf_counter() - started
        )
        logger.info(
            "Evaluation completed for {} in {:.2f}s", version, time.perf_counter() - started
        )
        return EvaluationResult(
            version=version,
            selected_model=str(metadata.get("selected_model", "unknown")),
            threshold=threshold,
            metrics_path=output / "metrics.json",
            evaluation_report=evaluation_report,
            model_card=model_card,
            shap_directory=shap_directory,
            experiment_history=experiment_history,
        )

    def _holdout(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        target = self.settings.dataset.target_column
        clean = frame.drop_duplicates().reset_index(drop=True)
        if target not in clean.columns:
            raise ValueError(f"Target column '{target}' is missing")
        X = clean.drop(columns=[target])
        y = clean[target].astype(int)
        _, X_test, _, y_test = train_test_split(
            X,
            y,
            test_size=self.settings.training.test_size,
            stratify=y,
            random_state=self.settings.training.random_state,
        )
        return X_test, y_test

    def _latest_version(self) -> str:
        versions = [
            path
            for path in self.settings.paths.models.glob("v*")
            if path.is_dir() and path.name[1:].isdigit()
        ]
        if not versions:
            raise FileNotFoundError("No versioned model found under the configured models path")
        return max(versions, key=lambda path: int(path.name[1:])).name

    def _optimize_threshold(self, y_true: pd.Series, probabilities: np.ndarray) -> float:
        evaluation = self.settings.evaluation
        strategy = evaluation.threshold_strategy.lower()
        if strategy == "business":
            return evaluation.business_threshold
        thresholds = np.linspace(0.01, 0.99, evaluation.threshold_grid_size)
        scores: list[float] = []
        for threshold in thresholds:
            predicted = (probabilities >= threshold).astype(int)
            precision = precision_score(y_true, predicted, zero_division=0)
            recall = recall_score(y_true, predicted, zero_division=0)
            if strategy in {"maximum_recall", "max_recall"}:
                score = recall
            elif strategy in {"balanced_precision_recall", "balanced"}:
                score = (
                    (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
                )
            else:
                score = f1_score(y_true, predicted, zero_division=0)
            scores.append(float(score))
        return float(thresholds[int(np.argmax(scores))])

    @staticmethod
    def _metrics(
        y_true: pd.Series, predictions: np.ndarray, probabilities: np.ndarray
    ) -> dict[str, float]:
        tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
        specificity = float(tn / (tn + fp)) if tn + fp else 0.0
        return {
            "accuracy": float(accuracy_score(y_true, predictions)),
            "precision": float(precision_score(y_true, predictions, zero_division=0)),
            "recall": float(recall_score(y_true, predictions, zero_division=0)),
            "f1": float(f1_score(y_true, predictions, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_true, probabilities)),
            "pr_auc": float(average_precision_score(y_true, probabilities)),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
            "matthews_correlation_coefficient": float(matthews_corrcoef(y_true, predictions)),
            "cohen_kappa": float(cohen_kappa_score(y_true, predictions)),
            "specificity": specificity,
            "sensitivity": float(recall_score(y_true, predictions, zero_division=0)),
            "true_negatives": float(tn),
            "false_positives": float(fp),
            "false_negatives": float(fn),
            "true_positives": float(tp),
        }

    @staticmethod
    def _write_metrics(metrics: dict[str, float], json_path: Path, csv_path: Path) -> None:
        json_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        with csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["metric", "value"])
            writer.writerows(metrics.items())

    def _write_threshold_report(
        self, y_true: pd.Series, probabilities: np.ndarray, path: Path
    ) -> None:
        thresholds = np.linspace(0.01, 0.99, self.settings.evaluation.threshold_grid_size)
        rows = []
        for threshold in thresholds:
            predictions = (probabilities >= threshold).astype(int)
            rows.append(
                {
                    "threshold": threshold,
                    "precision": precision_score(y_true, predictions, zero_division=0),
                    "recall": recall_score(y_true, predictions, zero_division=0),
                    "f1": f1_score(y_true, predictions, zero_division=0),
                }
            )
        pd.DataFrame(rows).to_csv(path, index=False)

    def _write_error_analysis(
        self,
        X: pd.DataFrame,
        y_true: pd.Series,
        probabilities: np.ndarray,
        predictions: np.ndarray,
        output: Path,
    ) -> None:
        analysis = X.reset_index(drop=True).copy()
        analysis["actual"] = y_true.reset_index(drop=True)
        analysis["probability"] = probabilities
        analysis["prediction"] = predictions
        analysis["error_type"] = np.select(
            [
                (analysis.actual == 0) & (analysis.prediction == 0),
                (analysis.actual == 0) & (analysis.prediction == 1),
                (analysis.actual == 1) & (analysis.prediction == 0),
                (analysis.actual == 1) & (analysis.prediction == 1),
            ],
            ["true_negative", "false_positive", "false_negative", "true_positive"],
            default="unknown",
        )
        analysis.to_csv(output / "error_analysis.csv", index=False)
        analysis[analysis.error_type.isin(["false_positive", "false_negative"])].to_csv(
            output / "misclassified_transactions.csv", index=False
        )
        counts = analysis["error_type"].value_counts().to_dict()
        report = "# Error Analysis Report\n\n" + "\n".join(
            f"- {key}: {value}" for key, value in counts.items()
        )
        (output / "error_analysis_report.md").write_text(report + "\n", encoding="utf-8")

    def _write_feature_importance(
        self, pipeline: Any, X: pd.DataFrame, plots: Path, output: Path
    ) -> None:
        features = pipeline.named_steps["features"].transform(X.head(1))
        transformed = pipeline.named_steps["preprocessing"].transform(features)
        names = pipeline.named_steps["preprocessing"].get_feature_names_out()
        model = pipeline.named_steps["model"]
        importance = getattr(model, "feature_importances_", None)
        if importance is None and hasattr(model, "coef_"):
            importance = np.abs(model.coef_[0])
        if importance is None:
            return
        importance_frame = pd.DataFrame({"feature": names, "importance": importance})
        importance_frame.sort_values("importance", ascending=False).to_csv(
            output / "feature_importance.csv", index=False
        )
        top = importance_frame.nlargest(20, "importance").sort_values("importance")
        plt.figure(figsize=(10, 8))
        sns.barplot(data=top, x="importance", y="feature", color="#2f6f73")
        plt.title("Feature Importance")
        plt.tight_layout()
        plt.savefig(plots / "feature_importance.png", dpi=160)
        plt.close()
        del transformed

    def _write_plots(
        self, y_true: pd.Series, probabilities: np.ndarray, predictions: np.ndarray, plots: Path
    ) -> None:
        matrix = confusion_matrix(y_true, predictions, labels=[0, 1])
        plt.figure(figsize=(6, 5))
        sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", cbar=False)
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
        plt.title("Confusion Matrix")
        plt.tight_layout()
        plt.savefig(plots / "confusion_matrix.png", dpi=160)
        plt.close()

        fpr, tpr, _ = roc_curve(y_true, probabilities)
        plt.figure(figsize=(7, 5))
        plt.plot(fpr, tpr, label=f"ROC AUC={roc_auc_score(y_true, probabilities):.4f}")
        plt.plot([0, 1], [0, 1], "--", color="grey")
        plt.xlabel("False positive rate")
        plt.ylabel("True positive rate")
        plt.title("ROC Curve")
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots / "roc_curve.png", dpi=160)
        plt.close()

        precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
        plt.figure(figsize=(7, 5))
        plt.plot(
            recall, precision, label=f"PR AUC={average_precision_score(y_true, probabilities):.4f}"
        )
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title("Precision Recall Curve")
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots / "precision_recall_curve.png", dpi=160)
        plt.close()

        threshold_frame = pd.DataFrame(
            {
                "threshold": thresholds,
                "precision": precision[:-1],
                "recall": recall[:-1],
            }
        )
        for column, filename, title in [
            ("precision", "precision_vs_threshold.png", "Precision vs Threshold"),
            ("recall", "recall_vs_threshold.png", "Recall vs Threshold"),
        ]:
            plt.figure(figsize=(7, 5))
            plt.plot(threshold_frame.threshold, threshold_frame[column])
            plt.xlabel("Threshold")
            plt.ylabel(column.title())
            plt.title(title)
            plt.tight_layout()
            plt.savefig(plots / filename, dpi=160)
            plt.close()

        fraction, mean = calibration_curve(
            y_true, probabilities, n_bins=self.settings.evaluation.calibration_bins
        )
        plt.figure(figsize=(7, 5))
        plt.plot(mean, fraction, marker="o", label="Model")
        plt.plot([0, 1], [0, 1], "--", color="grey", label="Perfectly calibrated")
        plt.xlabel("Mean predicted probability")
        plt.ylabel("Fraction of positives")
        plt.title("Calibration Curve")
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots / "calibration_curve.png", dpi=160)
        plt.close()

        plt.figure(figsize=(7, 5))
        sns.histplot(
            probabilities[y_true.to_numpy() == 0],
            color="#2f6f73",
            label="Normal",
            stat="density",
            alpha=0.5,
        )
        sns.histplot(
            probabilities[y_true.to_numpy() == 1],
            color="#c45b3c",
            label="Fraud",
            stat="density",
            alpha=0.5,
        )
        plt.xlabel("Predicted probability")
        plt.title("Prediction Probability Distribution")
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots / "prediction_probability_distribution.png", dpi=160)
        plt.close()

    def _write_shap(self, pipeline: Any, X: pd.DataFrame, plots: Path) -> Path:
        import shap

        shap_directory = self.settings.evaluation.shap_directory
        shap_directory.mkdir(parents=True, exist_ok=True)
        sample = X.sample(
            n=min(self.settings.evaluation.shap_sample_size, len(X)),
            random_state=self.settings.training.random_state,
        )
        engineered = pipeline.named_steps["features"].transform(sample)
        transformed = pipeline.named_steps["preprocessing"].transform(engineered)
        names = pipeline.named_steps["preprocessing"].get_feature_names_out()
        model = pipeline.named_steps["model"]
        try:
            explainer = shap.TreeExplainer(model)
            values = explainer.shap_values(transformed)
            base_value = explainer.expected_value
        except Exception:
            explainer = shap.Explainer(model, transformed)
            generic_explanation = explainer(transformed)
            values = generic_explanation.values
            base_value = generic_explanation.base_values
        if isinstance(values, list):
            values = values[1]
        if isinstance(base_value, list):
            base_value = base_value[1]
        explanation = shap.Explanation(
            values=np.asarray(values),
            base_values=np.repeat(base_value, len(transformed)),
            data=transformed,
            feature_names=names,
        )
        plt.figure()
        shap.summary_plot(values, transformed, feature_names=names, show=False)
        plt.tight_layout()
        plt.savefig(shap_directory / "summary_plot.png", dpi=160, bbox_inches="tight")
        plt.close()
        plt.figure()
        shap.summary_plot(values, transformed, feature_names=names, plot_type="bar", show=False)
        plt.tight_layout()
        plt.savefig(shap_directory / "bar_plot.png", dpi=160, bbox_inches="tight")
        plt.close()
        top_feature = int(np.abs(values).mean(axis=0).argmax())
        plt.figure()
        shap.dependence_plot(top_feature, values, transformed, feature_names=names, show=False)
        plt.tight_layout()
        plt.savefig(shap_directory / "dependence_plot.png", dpi=160, bbox_inches="tight")
        plt.close()
        shap.plots.waterfall(explanation[0], show=False, max_display=15)
        plt.tight_layout()
        plt.savefig(shap_directory / "waterfall_plot.png", dpi=160, bbox_inches="tight")
        plt.close()
        pd.DataFrame(
            np.abs(values).mean(axis=0), index=names, columns=["mean_abs_shap"]
        ).sort_values("mean_abs_shap", ascending=False).to_csv(
            shap_directory / "global_feature_importance.csv"
        )
        logger.info("SHAP completed; outputs written to {}", shap_directory)
        return shap_directory

    @staticmethod
    def _write_evaluation_report(
        version: str,
        metadata: dict[str, Any],
        metrics: dict[str, float],
        threshold: float,
        path: Path,
    ) -> Path:
        lines = [
            "# Evaluation Report",
            "",
            f"- Model version: `{version}`",
            f"- Algorithm: `{metadata.get('selected_model', 'unknown')}`",
            f"- Decision threshold: `{threshold:.4f}`",
            "",
            "## Metrics",
            "",
        ]
        lines.extend(f"- {key}: {value:.6f}" for key, value in metrics.items())
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def _write_model_card(
        version: str,
        metadata: dict[str, Any],
        metrics: dict[str, float],
        path: Path,
        dataset_filename: str,
    ) -> Path:
        content = (
            f"""# Model Card

## Model Details

- Version: `{version}`
- Algorithm: `{metadata.get('selected_model', 'unknown')}`
- Training date: `{metadata.get('timestamp_utc', 'unknown')}`
- Dataset: `{dataset_filename}`
- Dataset rows used for training: `{metadata.get('row_count', 'unknown')}`

## Hyperparameters and Configuration

```json
{json.dumps(metadata.get('training_configuration', {}), indent=2, default=str)}
```

## Intended Use

Fraud-risk research and controlled offline evaluation of transaction classification models.

## Performance

"""
            + "\n".join(f"- {key}: {value:.6f}" for key, value in metrics.items())
            + """

## Limitations

Metrics are measured on a deterministic holdout and may not represent future transaction
populations. Thresholds and costs require business validation before operational use.

## Ethical Considerations

Fraud decisions can affect customers and merchants. Human review, fairness assessment,
privacy controls, and documented appeal processes are required before deployment.
"""
        )
        path.write_text(content, encoding="utf-8")
        return path

    def _track_experiment(
        self,
        version: str,
        metadata: dict[str, Any],
        metrics: dict[str, float],
        threshold: float,
        duration: float,
    ) -> Path:
        path = self.settings.evaluation.experiment_history
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "version": version,
            "model": metadata.get("selected_model"),
            "metrics": metrics,
            "threshold": threshold,
            "evaluation_duration_seconds": duration,
            "training_duration_seconds": metadata.get("training_duration_seconds"),
            "configuration": metadata.get("training_configuration", {}),
        }
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, default=str) + "\n")
        logger.info("Experiment tracking updated at {}", path)
        return path
