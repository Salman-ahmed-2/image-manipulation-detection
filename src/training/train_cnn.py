"""Training pipeline for the custom CNN baseline model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import tensorflow as tf

from config import Config
from src.models.cnn_model import build_custom_cnn
from src.preprocessing.image_loader import load_image
from src.preprocessing.image_normalizer import normalize_image
from src.preprocessing.image_resizer import resize_image
from src.training.callbacks import get_callbacks
from src.utils.logger import get_logger

logger = get_logger(__name__)


def compute_class_weights(labels: list[int]) -> dict[int, float]:
    """Compute balanced class weights for binary classification.

    Args:
        labels: Ground-truth integer labels for the training split.

    Returns:
        A dictionary mapping class index to balancing weight.
    """
    if not labels:
        return {0: 1.0, 1: 1.0}

    class_counts = {0: labels.count(0), 1: labels.count(1)}
    total_examples = len(labels)
    weights = {}
    for class_id in (0, 1):
        class_count = class_counts.get(class_id, 0)
        if class_count == 0:
            weights[class_id] = 1.0
        else:
            weights[class_id] = total_examples / (2 * class_count)
    return weights


def _load_image_array(image_path: str | Path) -> np.ndarray:
    """Load an image from disk, resize it, and normalize it to a float32 array."""
    resolved_path = Path(image_path)
    if not resolved_path.is_absolute():
        resolved_path = Config.BASE_DIR / resolved_path
    elif not resolved_path.is_file():
        path_str = str(image_path)
        if "data/raw" in path_str:
            candidate = Config.BASE_DIR / path_str[path_str.index("data/raw"):]
            if candidate.is_file():
                resolved_path = candidate

    image = load_image(resolved_path)
    resized = resize_image(image, target_size=Config.TARGET_SIZE)
    array = np.asarray(resized, dtype=np.float32)
    return normalize_image(array, mode="standard")


def build_dataset_frame(
    split_csv: str | Path,
    split_name: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Load the specified split and return image arrays and integer labels.

    Args:
        split_csv: CSV file containing at least ``filepath`` and ``label`` columns.
        split_name: Logical split name, such as ``train`` or ``val``.

    Returns:
        A tuple of image arrays and labels for the selected split.
    """
    csv_path = Path(split_csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset split CSV not found: {csv_path}")

    dataframe = pd.read_csv(csv_path)
    required_columns = {"filepath", "label"}
    missing = sorted(required_columns - set(dataframe.columns))
    if missing:
        raise ValueError(f"Dataset split CSV is missing required columns: {missing}")

    subset = dataframe[dataframe.get("split", "train") == split_name].copy()
    if subset.empty:
        raise ValueError(f"No rows found for split '{split_name}' in {csv_path}")

    image_arrays = np.stack(
        [_load_image_array(path) for path in subset["filepath"].tolist()],
        axis=0,
    )
    labels = subset["label"].astype(int).to_numpy()
    return image_arrays, labels


def build_training_datasets(
    split_csv: str | Path,
) -> tuple[tf.data.Dataset, tf.data.Dataset, dict[int, float]]:
    """Construct TensorFlow datasets and class weights from the split CSV."""
    train_images, train_labels = build_dataset_frame(split_csv, "train")
    val_images, val_labels = build_dataset_frame(split_csv, "val")

    train_dataset = tf.data.Dataset.from_tensor_slices((train_images, train_labels))
    train_dataset = train_dataset.shuffle(buffer_size=len(train_images))
    train_dataset = train_dataset.batch(Config.BATCH_SIZE)
    train_dataset = train_dataset.prefetch(tf.data.AUTOTUNE)

    val_dataset = tf.data.Dataset.from_tensor_slices((val_images, val_labels))
    val_dataset = val_dataset.batch(Config.BATCH_SIZE)
    val_dataset = val_dataset.prefetch(tf.data.AUTOTUNE)

    class_weights = compute_class_weights(train_labels.tolist())
    return train_dataset, val_dataset, class_weights


def train_cnn(
    split_csv: str | Path = Config.SPLITS_DIR / "dataset_split.csv",
    model_name: str = "cnn_model",
    epochs: int = Config.DEFAULT_EPOCHS,
) -> tuple[tf.keras.Model, tf.keras.callbacks.History]:
    """Train the custom CNN model using the dataset split CSV.

    Args:
        split_csv: Path to the CSV containing image paths and labels.
        model_name: Basename used for the saved checkpoint and history log.
        epochs: Maximum number of training epochs.

    Returns:
        A trained Keras model and the corresponding training history object.
    """
    Config.init_app()
    train_dataset, val_dataset, class_weights = build_training_datasets(split_csv)
    model = build_custom_cnn(input_shape=Config.INPUT_SHAPE)
    callbacks = get_callbacks(model_name)

    history = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=epochs,
        callbacks=callbacks,
        class_weight=class_weights,
        verbose=1,
    )
    logger.info("Finished training '%s'; best checkpoint saved to %s", model_name, Config.MODEL_DIR)
    return model, history


if __name__ == "__main__":
    train_cnn()
