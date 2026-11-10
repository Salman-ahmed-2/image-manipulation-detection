"""Training callbacks for the custom CNN baseline model."""

from __future__ import annotations

from pathlib import Path

import tensorflow as tf

from config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_callbacks(model_name: str) -> list[tf.keras.callbacks.Callback]:
    """Return standard Keras callbacks for CNN training.

    Args:
        model_name: Base filename used when naming the saved checkpoint and log.

    Returns:
        A list of Keras callback objects for early stopping, checkpointing,
        learning-rate scheduling, and CSV logging.

    Raises:
        ValueError: If the model name is empty.
    """
    if not model_name:
        raise ValueError("model_name must be a non-empty string.")

    Config.init_app()
    checkpoint_path = Path(Config.MODEL_DIR) / f"{model_name}.keras"
    csv_path = Path(Config.PLOTS_DIR) / f"{model_name}_training_history.csv"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Configuring training callbacks for model '%s'", model_name)
    return [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=8,
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(checkpoint_path),
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1,
        ),
        tf.keras.callbacks.CSVLogger(filename=str(csv_path)),
    ]
