"""Confusion-matrix visualization utilities."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

_COUNT_KEYS = ("tn", "fp", "fn", "tp")


def plot_confusion_matrix(
    cm_dict: dict[str, int],
    model_name: str,
    output_path: Path,
) -> Path:
    """Render a labeled 2x2 confusion-matrix heatmap.

    Percentages are normalized by the number of examples in each actual class.

    Args:
        cm_dict: Confusion-matrix counts using ``tn``, ``fp``, ``fn``, and ``tp``.
        model_name: Name shown in the plot title.
        output_path: Destination PNG path.

    Returns:
        The path of the saved confusion-matrix image.

    Raises:
        ValueError: If counts are missing, negative, or not integer values.
        OSError: If the plot cannot be saved.
    """
    if set(cm_dict) != set(_COUNT_KEYS):
        raise ValueError(f"cm_dict must contain exactly these keys: {_COUNT_KEYS}.")
    counts = [cm_dict[key] for key in _COUNT_KEYS]
    if any(not isinstance(value, (int, np.integer)) or value < 0 for value in counts):
        raise ValueError("Confusion-matrix counts must be non-negative integers.")

    matrix = np.array([[cm_dict["tn"], cm_dict["fp"]], [cm_dict["fn"], cm_dict["tp"]]])
    row_totals = matrix.sum(axis=1, keepdims=True)
    percentages = np.divide(
        matrix * 100.0,
        row_totals,
        out=np.zeros_like(matrix, dtype=np.float64),
        where=row_totals != 0,
    )
    annotations = np.empty(matrix.shape, dtype=object)
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            annotations[row, column] = (
                f"{matrix[row, column]}\n({percentages[row, column]:.1f}%)"
            )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(6, 5))
    try:
        sns.heatmap(
            matrix,
            annot=annotations,
            fmt="",
            cmap="Blues",
            cbar=False,
            xticklabels=("Authentic", "Manipulated"),
            yticklabels=("Authentic", "Manipulated"),
            ax=axis,
        )
        axis.set(
            title=f"{model_name} Confusion Matrix",
            xlabel="Predicted label",
            ylabel="Actual label",
        )
        figure.tight_layout()
        figure.savefig(destination, dpi=Config.PLOT_DPI, bbox_inches="tight")
    except OSError as error:
        logger.error("Could not save confusion-matrix plot to %s: %s", destination, error)
        raise
    finally:
        plt.close(figure)
    return destination