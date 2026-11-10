"""Evaluate trained image-manipulation models on a configured dataset split."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Config
from src.data.dataset_loader import extract_label_from_filename
from src.evaluation.confusion_matrix import plot_confusion_matrix
from src.evaluation.metrics import compute_classification_metrics, compute_confusion_matrix
from src.evaluation.visualization import plot_roc_curve
from src.preprocessing.image_loader import load_image
from src.preprocessing.image_normalizer import prepare_tensor
from src.utils.logger import get_logger

logger = get_logger(__name__)

_MODEL_PATHS = {
    "cnn": Config.MODEL_PATH_CNN,
    "mobilenet": Config.MODEL_PATH_MOBILENET,
}
_MODEL_DISPLAY_NAMES = {
    "cnn": "Custom CNN",
    "mobilenet": "MobileNetV2",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file with its header as a list of row dictionaries.

    Args:
        path: CSV file to read.

    Returns:
        The CSV rows, with values represented as strings.

    Raises:
        OSError: If the file cannot be opened.
        csv.Error: If the CSV data is malformed.
    """
    with path.open(encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def _load_split_samples(split_name: str) -> list[tuple[Path, int]]:
    """Load image paths and binary labels from the split catalog or split folder.

    Args:
        split_name: Configured dataset partition to load.

    Returns:
        Image paths paired with their authentic/manipulated labels.

    Raises:
        FileNotFoundError: If catalog, inventory, or referenced images are missing.
        ValueError: If split records or labels are invalid or no samples are found.
    """
    if split_name not in Config.DATASET_SPLIT_NAMES:
        raise ValueError(f"Unknown dataset split {split_name!r}.")

    split_csv = Config.DATASET_SPLIT_PATH
    if split_csv.is_file():
        split_rows = _read_csv(split_csv)
        if not split_rows:
            raise ValueError(f"Dataset split catalog contains no rows: {split_csv}")
        inventory_by_id: dict[str, str] = {}
        if "filepath" not in split_rows[0]:
            inventory_path = Config.DATASET_INVENTORY_PATH
            if not inventory_path.is_file():
                raise FileNotFoundError(
                    f"Dataset inventory is required to resolve paths: {inventory_path}"
                )
            inventory_rows = _read_csv(inventory_path)
            inventory_by_id = {
                row["image_id"]: row["filepath"]
                for row in inventory_rows
                if row.get("image_id") and row.get("filepath")
            }

        samples: list[tuple[Path, int]] = []
        for row in split_rows:
            if row.get("split") != split_name:
                continue
            try:
                label = int(row["label"])
            except (KeyError, ValueError) as error:
                raise ValueError(f"Invalid label in dataset split row: {row}") from error
            if label not in {Config.AUTHENTIC_LABEL, Config.MANIPULATED_LABEL}:
                raise ValueError(f"Dataset split contains a non-binary label: {label}")
            filepath = row.get("filepath") or inventory_by_id.get(row.get("image_id", ""))
            if not filepath:
                raise ValueError(
                    f"No image path is available for split record {row.get('image_id')!r}."
                )
            image_path = Path(filepath)
            if not image_path.is_absolute():
                image_path = Config.BASE_DIR / image_path
            if not image_path.is_file():
                raise FileNotFoundError(f"Split image does not exist: {image_path}")
            samples.append((image_path, label))
        if not samples:
            raise ValueError(f"Dataset split {split_name!r} contains no images.")
        return samples

    split_directory = Config.SPLITS_DIR / split_name
    if not split_directory.is_dir():
        raise FileNotFoundError(
            f"Neither dataset split catalog nor split directory exists for {split_name!r}."
        )

    samples = []
    for image_path in sorted(split_directory.rglob("*")):
        if (
            not image_path.is_file()
            or image_path.suffix.lower() not in Config.DATASET_IMAGE_EXTENSIONS
        ):
            continue
        try:
            label = int(extract_label_from_filename(image_path.name)["label"])
        except ValueError:
            logger.warning("Skipping split image with unknown label prefix: %s", image_path.name)
            continue
        samples.append((image_path, label))
    if not samples:
        raise ValueError(f"Dataset split directory contains no labeled images: {split_directory}")
    return samples


def _load_model(model_name: str) -> Any:
    """Load one saved Keras model for this standalone evaluation run.

    Args:
        model_name: Configured model identifier.

    Returns:
        The loaded Keras model.

    Raises:
        FileNotFoundError: If the configured model file is missing.
        RuntimeError: If TensorFlow is unavailable.
    """
    model_path = _MODEL_PATHS[model_name]
    if not model_path.is_file():
        raise FileNotFoundError(f"Trained model file does not exist: {model_path}")
    try:
        from tensorflow.keras.models import load_model
    except ImportError as error:
        raise RuntimeError("TensorFlow is required to load trained evaluation models.") from error
    return load_model(model_path)


def _predict_probabilities(model: Any, model_name: str, inputs: np.ndarray) -> np.ndarray:
    """Run a batch through a binary classifier and validate its probabilities.

    Args:
        model: Loaded binary Keras classifier.
        model_name: Model identifier used in error messages.
        inputs: Preprocessed image batch.

    Returns:
        One validated manipulated-class probability per image.

    Raises:
        ValueError: If model outputs do not have a valid binary probability shape/range.
    """
    outputs = np.asarray(model.predict(inputs, verbose=0), dtype=np.float64)
    if outputs.shape == (len(inputs), 1):
        outputs = outputs[:, 0]
    if outputs.shape != (len(inputs),):
        raise ValueError(
            f"{model_name} must return one sigmoid probability per image; "
            f"received output shape {outputs.shape}."
        )
    if not np.isfinite(outputs).all() or ((outputs < 0.0) | (outputs > 1.0)).any():
        raise ValueError(f"{model_name} returned values outside the probability range [0, 1].")
    return outputs


def _append_results(
    split_name: str,
    results: dict[str, dict[str, float]],
    confusion_matrices: dict[str, dict[str, int]],
) -> None:
    """Append actual evaluation metrics to the project results log.

    Args:
        split_name: Name of the evaluated dataset partition.
        results: Metrics keyed by model identifier.
        confusion_matrices: Confusion counts keyed by model identifier.

    Raises:
        OSError: If the results document cannot be updated.
    """
    destination = Config.RESULTS_TEMPLATE_PATH
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with destination.open("a", encoding="utf-8") as results_file:
        results_file.write("\n\n## Evaluation Run Results\n\n")
        results_file.write(f"- Run time (UTC): {timestamp}\n- Split: `{split_name}`\n\n")
        results_file.write(
            "| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Specificity "
            "| TN | FP | FN | TP |\n"
        )
        results_file.write(
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n"
        )
        for model_name, metrics in results.items():
            counts = confusion_matrices[model_name]
            values = " | ".join(f"{metrics[key]:.6f}" for key in (
                "accuracy", "precision", "recall", "f1_score", "roc_auc", "specificity"
            ))
            results_file.write(
                f"| {_MODEL_DISPLAY_NAMES[model_name]} | {values} | "
                f"{counts['tn']} | {counts['fp']} | {counts['fn']} | {counts['tp']} |\n"
            )


def evaluate_models(
    model_names: tuple[str, ...],
    split_name: str = "test",
) -> dict[str, dict[str, float]]:
    """Evaluate one or both models while streaming the selected split once.

    Args:
        model_names: Model identifiers selected from ``cnn`` and ``mobilenet``.
        split_name: Dataset partition to evaluate. Defaults to the held-out test split.

    Returns:
        A mapping from model identifier to its computed classification metrics.

    Raises:
        FileNotFoundError: If model or dataset files are missing.
        ValueError: If split records, model outputs, or metrics are invalid.
        OSError: If plots or benchmark results cannot be written.
    """
    if not model_names or any(name not in _MODEL_PATHS for name in model_names):
        raise ValueError("model_names must contain 'cnn', 'mobilenet', or both.")
    if len(set(model_names)) != len(model_names):
        raise ValueError("model_names must not contain duplicates.")

    samples = _load_split_samples(split_name)
    models = {name: _load_model(name) for name in model_names}
    labels = np.asarray([label for _, label in samples], dtype=np.int64)
    probabilities: dict[str, list[np.ndarray]] = {name: [] for name in model_names}

    for batch_start in range(0, len(samples), Config.BATCH_SIZE):
        batch_samples = samples[batch_start : batch_start + Config.BATCH_SIZE]
        batch_inputs: dict[str, list[np.ndarray]] = {name: [] for name in model_names}
        for image_path, _ in batch_samples:
            image = load_image(image_path)
            for model_name in model_names:
                normalization_mode = "mobilenet" if model_name == "mobilenet" else "standard"
                tensor = prepare_tensor(image, mode=normalization_mode)
                batch_inputs[model_name].append(tensor[0])

        for model_name in model_names:
            input_array = np.stack(batch_inputs[model_name])
            probabilities[model_name].append(
                _predict_probabilities(models[model_name], model_name, input_array)
            )

    results: dict[str, dict[str, float]] = {}
    confusion_matrices: dict[str, dict[str, int]] = {}
    for model_name in model_names:
        model_probabilities = np.concatenate(probabilities[model_name])
        metrics = compute_classification_metrics(labels, model_probabilities)
        counts = compute_confusion_matrix(labels, model_probabilities)
        plot_confusion_matrix(
            counts,
            _MODEL_DISPLAY_NAMES[model_name],
            Config.PLOTS_DIR / f"{model_name}_confusion_matrix.png",
        )
        plot_roc_curve(
            labels,
            model_probabilities,
            _MODEL_DISPLAY_NAMES[model_name],
            Config.PLOTS_DIR / f"{model_name}_roc_curve.png",
        )
        results[model_name] = metrics
        confusion_matrices[model_name] = counts

    _append_results(split_name, results, confusion_matrices)
    return results


def _parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line options for model and split selection.

    Args:
        arguments: Optional command-line argument list; defaults to process arguments.

    Returns:
        Parsed model and split selections.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        choices=Config.EVALUATION_MODEL_CHOICES,
        default="both",
        help="Model to evaluate (default: both).",
    )
    parser.add_argument(
        "--split",
        choices=Config.DATASET_SPLIT_NAMES,
        default="test",
        help="Dataset split to evaluate (default: test).",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    """Run evaluation and print a formatted report to standard output."""
    options = _parse_args(arguments)
    model_names = (
        ("cnn", "mobilenet") if options.model == "both" else (options.model,)
    )
    results = evaluate_models(model_names, options.split)
    print(f"Evaluation results for split: {options.split}")
    for model_name, metrics in results.items():
        print(f"\n{_MODEL_DISPLAY_NAMES[model_name]}")
        for metric_name, value in metrics.items():
            print(f"  {metric_name.replace('_', ' ').title():<12} {value:.4f}")
    logger.info("Evaluation completed for split '%s' and models %s", options.split, model_names)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())