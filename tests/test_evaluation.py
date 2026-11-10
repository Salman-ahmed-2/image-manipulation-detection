"""Tests for classification metrics, visualizations, and evaluation orchestration."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from config import Config
from scripts import evaluate as evaluate_script
from src.evaluation.confusion_matrix import plot_confusion_matrix
from src.evaluation.metrics import compute_classification_metrics, compute_confusion_matrix
from src.evaluation.visualization import plot_roc_curve, plot_training_history


def test_compute_classification_metrics_matches_binary_definitions() -> None:
    """Compute standard metrics from synthetic labels and probabilities."""
    labels = np.array([0, 0, 1, 1])
    probabilities = np.array([0.1, 0.4, 0.8, 0.9])

    metrics = compute_classification_metrics(labels, probabilities)

    assert metrics == {
        "accuracy": 1.0,
        "precision": 1.0,
        "recall": 1.0,
        "f1_score": 1.0,
        "roc_auc": 1.0,
        "specificity": 1.0,
    }


def test_compute_classification_metrics_reports_zero_division_and_specificity() -> None:
    """Undefined positive-class ratios use zero while specificity remains defined."""
    metrics = compute_classification_metrics(
        np.array([0, 0, 1]),
        np.array([0.1, 0.3, 0.2]),
    )

    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["f1_score"] == 0.0
    assert metrics["specificity"] == 1.0


def test_compute_classification_metrics_rejects_single_class_auc() -> None:
    """ROC-AUC is not fabricated when only one ground-truth class is present."""
    with pytest.raises(ValueError):
        compute_classification_metrics(np.array([0, 0]), np.array([0.1, 0.2]))


@pytest.mark.parametrize(
    ("labels", "probabilities", "threshold"),
    [
        (np.array([]), np.array([]), 0.5),
        (np.array([0]), np.array([0.5, 0.6]), 0.5),
        (np.array([2]), np.array([0.5]), 0.5),
        (np.array([0]), np.array([1.2]), 0.5),
        (np.array([0]), np.array([0.5]), 1.1),
    ],
)
def test_compute_confusion_matrix_rejects_invalid_inputs(
    labels: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> None:
    """Reject invalid labels, probabilities, vector sizes, and thresholds."""
    with pytest.raises(ValueError):
        compute_confusion_matrix(labels, probabilities, threshold)


def test_compute_confusion_matrix_returns_named_counts() -> None:
    """Return all four confusion-matrix cells for a thresholded prediction."""
    counts = compute_confusion_matrix(
        np.array([0, 0, 1, 1]),
        np.array([0.1, 0.8, 0.2, 0.9]),
    )

    assert counts == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}


def test_plot_confusion_matrix_saves_png(tmp_path: Path) -> None:
    """Generate an annotated heatmap at the requested destination."""
    destination = tmp_path / "plots" / "cnn_confusion_matrix.png"

    result = plot_confusion_matrix(
        {"tn": 3, "fp": 1, "fn": 2, "tp": 4},
        "Custom CNN",
        destination,
    )

    assert result == destination
    assert destination.is_file()
    assert destination.stat().st_size > 0


def test_plot_confusion_matrix_rejects_invalid_counts(tmp_path: Path) -> None:
    """Reject malformed confusion-matrix count dictionaries."""
    with pytest.raises(ValueError, match="exactly these keys"):
        plot_confusion_matrix({"tn": 1}, "Custom CNN", tmp_path / "invalid.png")


def test_plot_roc_curve_saves_png(tmp_path: Path) -> None:
    """Generate a ROC curve with its AUC from synthetic predictions."""
    destination = tmp_path / "plots" / "cnn_roc_curve.png"

    result = plot_roc_curve(
        np.array([0, 0, 1, 1]),
        np.array([0.1, 0.4, 0.7, 0.9]),
        "Custom CNN",
        destination,
    )

    assert result == destination
    assert destination.is_file()
    assert destination.stat().st_size > 0


def test_plot_roc_curve_rejects_single_class(tmp_path: Path) -> None:
    """Do not generate a misleading ROC plot for a single-class dataset."""
    with pytest.raises(ValueError, match="both classes"):
        plot_roc_curve(
            np.array([0, 0]),
            np.array([0.1, 0.2]),
            "Custom CNN",
            tmp_path / "single_class.png",
        )


def test_plot_training_history_saves_side_by_side_plot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read synthetic CSVLogger data and save the combined history plot."""
    history_path = tmp_path / "training.csv"
    history_path.write_text(
        "epoch,loss,accuracy,val_loss,val_accuracy\n"
        "0,0.8,0.6,0.9,0.5\n"
        "1,0.4,0.8,0.6,0.7\n",
        encoding="utf-8",
    )
    plots_dir = tmp_path / "plots"
    monkeypatch.setattr(Config, "PLOTS_DIR", plots_dir)

    result = plot_training_history(history_path, "cnn")

    assert result == plots_dir / "cnn_training_history.png"
    assert result.is_file()
    assert result.stat().st_size > 0


def test_plot_training_history_rejects_missing_columns(tmp_path: Path) -> None:
    """Require loss and accuracy values for both training and validation."""
    history_path = tmp_path / "incomplete.csv"
    history_path.write_text("epoch,loss\n0,0.8\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        plot_training_history(history_path, "cnn")


def test_evaluate_models_streams_synthetic_split_and_appends_real_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Evaluate both fake models on synthetic images and write actual test metrics."""
    image_paths = (tmp_path / "Au_ani_0001.jpg", tmp_path / "Tp_D_ani_0002.jpg")
    for image_path, color in zip(image_paths, ((20, 40, 60), (200, 180, 160))):
        Image.new("RGB", (8, 8), color=color).save(image_path, format="JPEG")

    split_path = tmp_path / "dataset_split.csv"
    with split_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=("image_id", "label", "split"))
        writer.writeheader()
        writer.writerows(
            (
                {"image_id": "image-0", "label": 0, "split": "test"},
                {"image_id": "image-1", "label": 1, "split": "test"},
            )
        )
    inventory_path = tmp_path / "dataset_inventory.csv"
    with inventory_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=("image_id", "filepath"))
        writer.writeheader()
        writer.writerows(
            (
                {"image_id": "image-0", "filepath": str(image_paths[0])},
                {"image_id": "image-1", "filepath": str(image_paths[1])},
            )
        )
    results_path = tmp_path / "RESULTS_TEMPLATE.md"
    results_path.write_text("Results\n", encoding="utf-8")
    plots_path = tmp_path / "plots"
    monkeypatch.setattr(Config, "DATASET_SPLIT_PATH", split_path)
    monkeypatch.setattr(Config, "DATASET_INVENTORY_PATH", inventory_path)
    monkeypatch.setattr(Config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(Config, "RESULTS_TEMPLATE_PATH", results_path)
    monkeypatch.setattr(Config, "PLOTS_DIR", plots_path)
    monkeypatch.setattr(Config, "BATCH_SIZE", 2)

    class SyntheticModel:
        """Return deterministic probabilities for a synthetic batch."""

        def __init__(self, probabilities: tuple[float, float]) -> None:
            self.probabilities = probabilities

        def predict(self, inputs: np.ndarray, verbose: int = 0) -> np.ndarray:
            """Produce one probability per input image."""
            return np.asarray(self.probabilities[: len(inputs)]).reshape(-1, 1)

    monkeypatch.setattr(
        evaluate_script,
        "_load_model",
        lambda name: SyntheticModel((0.1, 0.9) if name == "cnn" else (0.2, 0.8)),
    )

    results = evaluate_script.evaluate_models(("cnn", "mobilenet"), "test")

    assert results["cnn"]["accuracy"] == 1.0
    assert results["mobilenet"]["roc_auc"] == 1.0
    assert (plots_path / "cnn_confusion_matrix.png").is_file()
    assert (plots_path / "mobilenet_roc_curve.png").is_file()
    recorded_results = results_path.read_text(encoding="utf-8")
    assert "Custom CNN" in recorded_results
    assert "MobileNetV2" in recorded_results
    assert "ROC-AUC" in recorded_results


def test_load_split_samples_rejects_missing_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail clearly if split metadata has no paths and its inventory is absent."""
    split_path = tmp_path / "dataset_split.csv"
    split_path.write_text("image_id,label,split\nimage-0,0,test\n", encoding="utf-8")
    monkeypatch.setattr(Config, "DATASET_SPLIT_PATH", split_path)
    monkeypatch.setattr(Config, "DATASET_INVENTORY_PATH", tmp_path / "missing.csv")

    with pytest.raises(FileNotFoundError, match="inventory"):
        evaluate_script._load_split_samples("test")
