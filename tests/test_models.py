"""Tests for model-building and CNN forward-pass correctness."""

from __future__ import annotations

import numpy as np
import tensorflow as tf

from src.models.cnn_model import build_custom_cnn
from src.training.callbacks import get_callbacks


def test_custom_cnn_builds_and_compiles() -> None:
    """Build the custom CNN and inspect its compiled graph structure."""
    model = build_custom_cnn()

    assert model.input_shape == (None, 224, 224, 3)
    assert model.output_shape == (None, 1)
    assert model.loss == "binary_crossentropy"
    assert len(model.metrics) >= 2
    assert model.optimizer is not None
    assert np.isclose(float(model.optimizer.learning_rate), 1e-3)


def test_custom_cnn_forward_pass_outputs_valid_probabilities() -> None:
    """Run a forward pass and verify that sigmoid outputs remain in range."""
    model = build_custom_cnn()
    logits = model(tf.zeros((2, 224, 224, 3)))

    assert logits.shape == (2, 1)
    assert np.all(logits.numpy() >= 0.0)
    assert np.all(logits.numpy() <= 1.0)


def test_get_callbacks_returns_expected_keras_callbacks() -> None:
    """Verify callback factory returns expected training controls."""
    callbacks = get_callbacks("test_cnn")

    callback_names = {type(callback).__name__ for callback in callbacks}
    assert {"EarlyStopping", "ModelCheckpoint", "ReduceLROnPlateau", "CSVLogger"}.issubset(
        callback_names
    )
