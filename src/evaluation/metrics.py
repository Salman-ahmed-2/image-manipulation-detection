"""Classification metrics for binary model evaluation."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from config import Config


def _validate_inputs(
    y_true: np.ndarray,
    y_pred_prob: np.ndarray,
    threshold: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate inputs shared by binary metric calculations.

    Args:
        y_true: Ground-truth labels to validate.
        y_pred_prob: Class-1 probabilities to validate.
        threshold: Classification threshold to validate.

    Returns:
        Flattened integer labels and float64 probabilities.

    Raises:
        ValueError: If an input is empty, misaligned, non-binary, or out of range.
    """
    labels = np.asarray(y_true).reshape(-1)
    probabilities = np.asarray(y_pred_prob, dtype=np.float64).reshape(-1)
    if labels.size == 0 or probabilities.size == 0:
        raise ValueError("y_true and y_pred_prob must not be empty.")
    if labels.size != probabilities.size:
        raise ValueError("y_true and y_pred_prob must contain the same number of values.")
    if not np.isin(labels, (0, 1)).all():
        raise ValueError("y_true values must be binary labels 0 or 1.")
    if not np.isfinite(probabilities).all() or (
        (probabilities < 0.0) | (probabilities > 1.0)
    ).any():
        raise ValueError("y_pred_prob values must be finite probabilities in [0, 1].")
    if not np.isfinite(threshold) or not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be a finite value in [0, 1].")
    return labels.astype(np.int64), probabilities


def compute_confusion_matrix(
    y_true: np.ndarray,
    y_pred_prob: np.ndarray,
    threshold: float = Config.CLASSIFICATION_THRESHOLD,
) -> dict[str, int]:
    """Compute binary confusion-matrix counts at a probability threshold.

    Args:
        y_true: Ground-truth binary labels, where 0 is authentic and 1 is manipulated.
        y_pred_prob: Predicted probabilities for the manipulated class.
        threshold: Probability boundary for classifying an image as manipulated.
            Defaults to ``Config.CLASSIFICATION_THRESHOLD``.

    Returns:
        A dictionary containing true-negative, false-positive, false-negative,
        and true-positive counts.

    Raises:
        ValueError: If labels, probabilities, or threshold are invalid.
    """
    labels, probabilities = _validate_inputs(y_true, y_pred_prob, threshold)
    predicted_labels = (probabilities >= threshold).astype(np.int64)
    tn, fp, fn, tp = confusion_matrix(labels, predicted_labels, labels=[0, 1]).ravel()
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred_prob: np.ndarray,
    threshold: float = Config.CLASSIFICATION_THRESHOLD,
) -> dict[str, float]:
    """Compute standard binary classification metrics.

    Args:
        y_true: Ground-truth binary labels, where 0 is authentic and 1 is manipulated.
        y_pred_prob: Predicted probabilities for the manipulated class.
        threshold: Probability boundary for classifying an image as manipulated.
            Defaults to ``Config.CLASSIFICATION_THRESHOLD``.

    Returns:
        Accuracy, precision, recall, F1-score, ROC-AUC, and specificity.

    Raises:
        ValueError: If labels, probabilities, or threshold are invalid, or the
            labels contain only one class so ROC-AUC cannot be computed.
    """
    labels, probabilities = _validate_inputs(y_true, y_pred_prob, threshold)
    if np.unique(labels).size != 2:
        raise ValueError("ROC-AUC requires ground-truth samples from both classes.")
    predicted_labels = (probabilities >= threshold).astype(np.int64)
    tn, fp, fn, tp = confusion_matrix(labels, predicted_labels, labels=[0, 1]).ravel()

    return {
        "accuracy": float(accuracy_score(labels, predicted_labels)),
        "precision": float(precision_score(labels, predicted_labels, zero_division=0)),
        "recall": float(recall_score(labels, predicted_labels, zero_division=0)),
        "f1_score": float(f1_score(labels, predicted_labels, zero_division=0)),
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "specificity": float(tn / (tn + fp)) if tn + fp else 0.0,
    }