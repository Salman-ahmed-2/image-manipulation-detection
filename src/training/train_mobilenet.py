"""Two-phase training pipeline for the MobileNetV2 transfer-learning model."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf

from config import Config
from src.models.mobilenet_model import build_mobilenet_model, unfreeze_mobilenet_layers
from src.preprocessing.image_loader import load_image
from src.preprocessing.image_normalizer import normalize_image
from src.preprocessing.image_resizer import resize_image
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _load_image_array(image_path: str | Path) -> np.ndarray:
    """Load, resize, and MobileNetV2-normalize one training image.

    Args:
        image_path: Path to an image listed in the dataset split CSV.

    Returns:
        A float32 RGB array scaled to the MobileNetV2 range of [-1, 1].
    """
    resolved_path = Path(image_path)
    if not resolved_path.is_absolute():
        resolved_path = Config.BASE_DIR / resolved_path

    image = load_image(resolved_path)
    resized = resize_image(image, target_size=Config.TARGET_SIZE)
    array = np.asarray(resized, dtype=np.float32)
    return normalize_image(array, mode=Config.MOBILENET_NORMALIZATION_MODE)


def build_dataset_frame(
    split_csv: str | Path,
    split_name: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Load the selected dataset split as normalized image arrays and labels.

    Args:
        split_csv: CSV containing ``label`` and ``split`` plus either ``filepath``
            or ``image_id`` columns. Image identifiers are resolved through the
            configured dataset inventory when necessary.
        split_name: Split name, such as ``train`` or ``validation``.

    Returns:
        A tuple containing the image array batch and integer labels.

    Raises:
        FileNotFoundError: If the split CSV does not exist.
        ValueError: If required columns or rows are missing, or labels are invalid.
    """
    csv_path = Path(split_csv)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Dataset split CSV not found: {csv_path}")

    dataframe = pd.read_csv(csv_path)
    required_columns = {"label", "split"}
    missing_columns = sorted(required_columns - set(dataframe.columns))
    if missing_columns:
        raise ValueError(f"Dataset split CSV is missing required columns: {missing_columns}")

    subset = dataframe[dataframe["split"] == split_name]
    if subset.empty:
        raise ValueError(f"No rows found for split {split_name!r} in {csv_path}")

    if "filepath" not in subset.columns:
        if "image_id" not in subset.columns:
            raise ValueError("Dataset split CSV must contain either filepath or image_id.")

        inventory_path = Path(Config.DATASET_INVENTORY_PATH)
        if not inventory_path.is_file():
            raise FileNotFoundError(f"Dataset inventory CSV not found: {inventory_path}")
        inventory = pd.read_csv(inventory_path)
        inventory_columns = {"image_id", "filepath"}
        missing_inventory_columns = sorted(inventory_columns - set(inventory.columns))
        if missing_inventory_columns:
            raise ValueError(
                "Dataset inventory CSV is missing required columns: "
                f"{missing_inventory_columns}"
            )
        subset = subset.merge(
            inventory.loc[:, ["image_id", "filepath"]],
            on="image_id",
            how="left",
            validate="many_to_one",
        )
    if subset["filepath"].isna().any() or subset["filepath"].eq("").any():
        raise ValueError(f"Dataset split {split_name!r} contains a missing image path.")

    labels = subset["label"].astype(int).to_numpy()
    valid_labels = {Config.AUTHENTIC_LABEL, Config.MANIPULATED_LABEL}
    if not set(np.unique(labels)).issubset(valid_labels):
        raise ValueError(f"Dataset split {split_name!r} contains unsupported labels.")

    image_arrays = np.stack(
        [_load_image_array(path) for path in subset["filepath"].tolist()],
        axis=0,
    )
    return image_arrays, labels


def build_training_datasets(
    split_csv: str | Path,
) -> tuple[tf.data.Dataset, tf.data.Dataset]:
    """Build shuffled training and deterministic validation TensorFlow datasets.

    Args:
        split_csv: CSV containing the train and validation dataset partitions.

    Returns:
        A tuple containing batched training and validation datasets.
    """
    train_name, validation_name, _ = Config.DATASET_SPLIT_NAMES
    train_images, train_labels = build_dataset_frame(split_csv, train_name)
    validation_images, validation_labels = build_dataset_frame(split_csv, validation_name)

    train_dataset = tf.data.Dataset.from_tensor_slices((train_images, train_labels))
    train_dataset = train_dataset.shuffle(
        buffer_size=len(train_images),
        seed=Config.RANDOM_SEED,
    )
    train_dataset = train_dataset.batch(Config.BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

    validation_dataset = tf.data.Dataset.from_tensor_slices(
        (validation_images, validation_labels)
    )
    validation_dataset = validation_dataset.batch(Config.BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    return train_dataset, validation_dataset


def train_mobilenet(
    split_csv: str | Path = Config.DATASET_SPLIT_PATH,
) -> tuple[tf.keras.Model, tuple[tf.keras.callbacks.History, tf.keras.callbacks.History]]:
    """Train MobileNetV2 in frozen-base and partial fine-tuning phases.

    Args:
        split_csv: CSV containing the train, validation, and test partitions.
            Defaults to ``Config.DATASET_SPLIT_PATH``.

    Returns:
        The trained model and a pair of Keras histories for both phases.
    """
    Config.init_app()
    train_dataset, validation_dataset = build_training_datasets(split_csv)
    model = build_mobilenet_model(input_shape=Config.INPUT_SHAPE)

    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        filepath=str(Config.MODEL_PATH_MOBILENET),
        monitor="val_loss",
        save_best_only=True,
        verbose=1,
    )
    phase_one_callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=Config.MOBILENET_EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
            verbose=1,
        ),
        checkpoint,
    ]
    logger.info("Starting MobileNetV2 feature-extraction phase")
    phase_one_history = model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=Config.MOBILENET_WARMUP_EPOCHS,
        callbacks=phase_one_callbacks,
        verbose=1,
    )

    model = unfreeze_mobilenet_layers(
        model,
        num_layers_to_unfreeze=Config.MOBILENET_LAYERS_TO_UNFREEZE,
        fine_tune_lr=Config.MOBILENET_FINE_TUNE_LEARNING_RATE,
    )
    phase_two_callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=Config.MOBILENET_EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
            verbose=1,
        ),
        checkpoint,
    ]
    logger.info("Starting MobileNetV2 fine-tuning phase")
    phase_two_history = model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=Config.MOBILENET_FINE_TUNE_EPOCHS,
        callbacks=phase_two_callbacks,
        verbose=1,
    )
    logger.info("MobileNetV2 best checkpoint saved to %s", Config.MODEL_PATH_MOBILENET)
    return model, (phase_one_history, phase_two_history)


if __name__ == "__main__":
    train_mobilenet()