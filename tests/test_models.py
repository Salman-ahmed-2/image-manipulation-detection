"""Tests for model-building and CNN forward-pass correctness."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
import tensorflow as tf
from PIL import Image

from config import Config
from src.models.cnn_model import build_custom_cnn
from src.models.mobilenet_model import build_mobilenet_model, unfreeze_mobilenet_layers
from src.training.callbacks import get_callbacks
from src.training import train_mobilenet as mobilenet_training


def _build_mobilenet_without_download(monkeypatch: pytest.MonkeyPatch) -> tf.keras.Model:
    """Build MobileNetV2 with random weights while verifying ImageNet is requested."""
    applications = tf.keras.applications
    original_builder = applications.MobileNetV2
    requested_weights: list[str | None] = []

    def build_without_download(
        input_shape: tuple[int, int, int],
        include_top: bool,
        weights: str | None,
        name: str,
    ) -> tf.keras.Model:
        """Replace ImageNet weights with random initialization for isolated tests."""
        requested_weights.append(weights)
        return original_builder(
            input_shape=input_shape,
            include_top=include_top,
            weights=None,
            name=name,
        )

    monkeypatch.setattr(applications, "MobileNetV2", build_without_download)
    model = build_mobilenet_model()
    assert requested_weights == [Config.MOBILENET_WEIGHTS]
    return model


def test_custom_cnn_builds_and_compiles() -> None:
    """Build the custom CNN and inspect its compiled graph structure."""
    model = build_custom_cnn()

    assert model.input_shape == (None, 224, 224, 3)
    assert model.output_shape == (None, Config.MOBILENET_OUTPUT_UNITS)
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


def test_mobilenet_builds_expected_classifier_head(monkeypatch: pytest.MonkeyPatch) -> None:
    """Build MobileNetV2 and verify the binary classification head structure."""
    model = _build_mobilenet_without_download(monkeypatch)

    assert model.input_shape == (None, *Config.INPUT_SHAPE)
    assert model.output_shape == (None, 1)
    assert model.loss == "binary_crossentropy"
    assert np.isclose(float(model.optimizer.learning_rate), Config.MOBILENET_INITIAL_LEARNING_RATE)
    assert any(isinstance(layer, tf.keras.layers.GlobalAveragePooling2D) for layer in model.layers)

    dense_layers = [layer for layer in model.layers if isinstance(layer, tf.keras.layers.Dense)]
    assert [layer.units for layer in dense_layers] == [
        *Config.MOBILENET_HEAD_UNITS,
        Config.MOBILENET_OUTPUT_UNITS,
    ]
    assert [layer.rate for layer in model.layers if isinstance(layer, tf.keras.layers.Dropout)] == [
        *Config.MOBILENET_HEAD_DROPOUT_RATES
    ]


def test_mobilenet_base_layers_start_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify every MobileNetV2 backbone layer is frozen during classifier warmup."""
    model = _build_mobilenet_without_download(monkeypatch)
    base_model = model.get_layer(Config.MOBILENET_BASE_MODEL_NAME)

    assert not base_model.trainable
    assert all(not layer.trainable for layer in base_model.layers)


def test_mobilenet_unfreezes_exactly_top_layers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify fine-tuning activates only the requested trailing backbone layers."""
    model = _build_mobilenet_without_download(monkeypatch)
    base_model = model.get_layer(Config.MOBILENET_BASE_MODEL_NAME)
    number_to_unfreeze = Config.MOBILENET_LAYERS_TO_UNFREEZE

    returned_model = unfreeze_mobilenet_layers(model, num_layers_to_unfreeze=number_to_unfreeze)

    trainable_layers = [layer for layer in base_model.layers if layer.trainable]
    assert returned_model is model
    assert len(trainable_layers) == number_to_unfreeze
    assert all(layer.trainable for layer in base_model.layers[-number_to_unfreeze:])
    assert all(not layer.trainable for layer in base_model.layers[:-number_to_unfreeze])
    assert np.isclose(
        float(model.optimizer.learning_rate),
        Config.MOBILENET_FINE_TUNE_LEARNING_RATE,
    )


def test_mobilenet_forward_pass_returns_probability(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run a synthetic input through MobileNetV2 and check its sigmoid output."""
    model = _build_mobilenet_without_download(monkeypatch)
    output = model(tf.zeros((1, *Config.INPUT_SHAPE)), training=False).numpy()

    assert output.shape == (1, 1)
    assert np.all(output >= 0.0)
    assert np.all(output <= 1.0)


def test_mobilenet_unfreeze_rejects_invalid_layer_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject layer counts that cannot describe a valid backbone subset."""
    model = _build_mobilenet_without_download(monkeypatch)

    with pytest.raises(ValueError, match="num_layers_to_unfreeze"):
        unfreeze_mobilenet_layers(model, num_layers_to_unfreeze=-1)


def test_mobilenet_training_uses_mobilenet_normalization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify MobileNet training preprocessing applies the [-1, 1] scale in memory."""
    synthetic_image = Image.new("RGB", Config.TARGET_SIZE, color=(128, 128, 128))
    monkeypatch.setattr(
        mobilenet_training,
        "load_image",
        Mock(return_value=synthetic_image),
    )

    image_array = mobilenet_training._load_image_array("synthetic-image.jpg")

    assert image_array.shape == (*Config.TARGET_SIZE[::-1], Config.INPUT_SHAPE[-1])
    assert image_array.dtype == np.float32
    expected_value = (128 / (Config.PIXEL_VALUE_MAX / 2)) - 1
    assert np.isclose(image_array.min(), expected_value, atol=1e-6)
    assert np.isclose(image_array.max(), expected_value, atol=1e-6)


def test_mobilenet_training_resolves_split_ids_from_inventory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Resolve filepath values from the inventory for the configured split schema."""
    split_csv = tmp_path / "dataset_split.csv"
    inventory_csv = tmp_path / "dataset_inventory.csv"
    pd.DataFrame(
        {"image_id": ["synthetic:one"], "label": [Config.AUTHENTIC_LABEL], "split": ["train"]}
    ).to_csv(split_csv, index=False)
    pd.DataFrame(
        {"image_id": ["synthetic:one"], "filepath": ["synthetic-image.jpg"]}
    ).to_csv(inventory_csv, index=False)
    monkeypatch.setattr(Config, "DATASET_INVENTORY_PATH", inventory_csv)
    synthetic_array = np.zeros(
        (*Config.TARGET_SIZE[::-1], Config.INPUT_SHAPE[-1]),
        dtype=np.float32,
    )
    load_array = Mock(return_value=synthetic_array)
    monkeypatch.setattr(mobilenet_training, "_load_image_array", load_array)

    images, labels = mobilenet_training.build_dataset_frame(split_csv, "train")

    assert images.shape == (1, *synthetic_array.shape)
    assert labels.tolist() == [Config.AUTHENTIC_LABEL]
    load_array.assert_called_once_with("synthetic-image.jpg")


def test_mobilenet_training_runs_both_phases(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify the training entry point runs warmup and fine-tuning with checkpoints."""
    model = Mock()
    phase_one_history = Mock()
    phase_two_history = Mock()
    model.fit.side_effect = [phase_one_history, phase_two_history]
    monkeypatch.setattr(Config, "init_app", lambda app=None: None)
    monkeypatch.setattr(Config, "MODEL_PATH_MOBILENET", tmp_path / "mobilenet_model.keras")
    monkeypatch.setattr(
        mobilenet_training,
        "build_training_datasets",
        lambda _: (object(), object()),
    )
    monkeypatch.setattr(mobilenet_training, "build_mobilenet_model", lambda **_: model)
    unfreeze = Mock(return_value=model)
    monkeypatch.setattr(mobilenet_training, "unfreeze_mobilenet_layers", unfreeze)

    returned_model, histories = mobilenet_training.train_mobilenet("synthetic-split.csv")

    assert returned_model is model
    assert histories == (phase_one_history, phase_two_history)
    assert [call.kwargs["epochs"] for call in model.fit.call_args_list] == [
        Config.MOBILENET_WARMUP_EPOCHS,
        Config.MOBILENET_FINE_TUNE_EPOCHS,
    ]
    assert unfreeze.call_args.kwargs == {
        "num_layers_to_unfreeze": Config.MOBILENET_LAYERS_TO_UNFREEZE,
        "fine_tune_lr": Config.MOBILENET_FINE_TUNE_LEARNING_RATE,
    }
    phase_one_checkpoint = model.fit.call_args_list[0].kwargs["callbacks"][1]
    phase_two_checkpoint = model.fit.call_args_list[1].kwargs["callbacks"][1]
    assert isinstance(phase_one_checkpoint, tf.keras.callbacks.ModelCheckpoint)
    assert phase_one_checkpoint is phase_two_checkpoint
    assert phase_one_checkpoint.filepath == str(Config.MODEL_PATH_MOBILENET)
