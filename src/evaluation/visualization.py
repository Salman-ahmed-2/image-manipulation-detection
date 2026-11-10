"""ROC and training-history visualization utilities."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import auc, roc_curve

from config import Config
from src.evaluation.metrics import _validate_inputs
from src.utils.logger import get_logger

logger = get_logger(__name__)


def plot_roc_curve(
    y_true: np.ndarray,
    y_pred_prob: np.ndarray,
    model_name: str,
    output_path: Path,
) -> Path:
    """Plot and save a receiver operating characteristic curve.

    Args:
        y_true: Ground-truth binary labels, where 0 is authentic and 1 is manipulated.
        y_pred_prob: Predicted probabilities for the manipulated class.
        model_name: Name shown in the plot title and legend.
        output_path: Destination PNG path.

    Returns:
        The path of the saved ROC-curve image.

    Raises:
        ValueError: If inputs are invalid or labels contain only one class.
        OSError: If the plot cannot be saved.
    """
    labels, probabilities = _validate_inputs(y_true, y_pred_prob, Config.CLASSIFICATION_THRESHOLD)
    if np.unique(labels).size != 2:
        raise ValueError("ROC curve requires ground-truth samples from both classes.")
    false_positive_rate, true_positive_rate, _ = roc_curve(labels, probabilities)
    roc_auc = auc(false_positive_rate, true_positive_rate)

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(6, 5))
    try:
        axis.plot(
            false_positive_rate,
            true_positive_rate,
            label=f"{model_name} (AUC = {roc_auc:.3f})",
        )
        axis.plot((0.0, 1.0), (0.0, 1.0), linestyle="--", color="gray", label="Chance")
        axis.set(
            title=f"{model_name} ROC Curve",
            xlabel="False Positive Rate",
            ylabel="True Positive Rate",
            xlim=(0.0, 1.0),
            ylim=(0.0, 1.05),
        )
        axis.legend(loc="lower right")
        figure.tight_layout()
        figure.savefig(destination, dpi=Config.PLOT_DPI, bbox_inches="tight")
    except OSError as error:
        logger.error("Could not save ROC plot to %s: %s", destination, error)
        raise
    finally:
        plt.close(figure)
    return destination


def plot_training_history(history_csv: Path, model_name: str) -> Path:
    """Plot training and validation loss and accuracy from a CSVLogger file.

    Args:
        history_csv: Path to the CSV file produced by Keras ``CSVLogger``.
        model_name: Name shown in the plot title and output filename.

    Returns:
        The path of the saved training-history image in ``Config.PLOTS_DIR``.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required loss or accuracy columns are missing.
        OSError: If the plot cannot be saved.
    """
    history_path = Path(history_csv)
    if not history_path.is_file():
        raise FileNotFoundError(f"Training history CSV does not exist: {history_path}")
    history = pd.read_csv(history_path)
    if history.empty:
        raise ValueError("Training history CSV contains no epoch records.")
    accuracy_column = "accuracy" if "accuracy" in history.columns else "binary_accuracy"
    validation_accuracy_column = (
        "val_accuracy" if "val_accuracy" in history.columns else "val_binary_accuracy"
    )
    required_columns = {"loss", "val_loss", accuracy_column, validation_accuracy_column}
    missing_columns = required_columns.difference(history.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Training history is missing required columns: {missing}.")

    epochs = np.arange(1, len(history) + 1)
    destination = Config.PLOTS_DIR / f"{model_name}_training_history.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    try:
        axes[0].plot(epochs, history["loss"], label="Training")
        axes[0].plot(epochs, history["val_loss"], label="Validation")
        axes[0].set(title="Loss", xlabel="Epoch", ylabel="Loss")
        axes[0].legend()
        axes[1].plot(epochs, history[accuracy_column], label="Training")
        axes[1].plot(epochs, history[validation_accuracy_column], label="Validation")
        axes[1].set(title="Accuracy", xlabel="Epoch", ylabel="Accuracy")
        axes[1].legend()
        figure.suptitle(f"{model_name} Training History")
        figure.tight_layout()
        figure.savefig(destination, dpi=Config.PLOT_DPI, bbox_inches="tight")
    except OSError as error:
        logger.error("Could not save training-history plot to %s: %s", destination, error)
        raise
    finally:
        plt.close(figure)
    return destination