"""MobileNetV2 transfer-learning architecture for binary image classification."""

from __future__ import annotations

import math
from numbers import Integral, Real

import tensorflow as tf

from config import Config


def build_mobilenet_model(
    input_shape: tuple[int, int, int] = Config.INPUT_SHAPE,
) -> tf.keras.Model:
    """Build a MobileNetV2 binary classifier with a frozen ImageNet backbone.

    Args:
        input_shape: Input dimensions in ``(height, width, channels)`` order.
            Defaults to ``Config.INPUT_SHAPE``.

    Returns:
        A compiled Keras model with a frozen MobileNetV2 base and trainable
        binary classification head.

    Raises:
        ValueError: If input_shape does not contain three positive integers.
    """
    if len(input_shape) != 3 or any(
        not isinstance(dimension, Integral)
        or isinstance(dimension, bool)
        or dimension <= 0
        for dimension in input_shape
    ):
        raise ValueError("input_shape must contain three positive integer dimensions.")

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights=Config.MOBILENET_WEIGHTS,
        name=Config.MOBILENET_BASE_MODEL_NAME,
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=input_shape)
    x = base_model(inputs)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(Config.MOBILENET_HEAD_UNITS[0], activation="relu")(x)
    x = tf.keras.layers.Dropout(Config.MOBILENET_HEAD_DROPOUT_RATES[0])(x)
    x = tf.keras.layers.Dense(Config.MOBILENET_HEAD_UNITS[1], activation="relu")(x)
    x = tf.keras.layers.Dropout(Config.MOBILENET_HEAD_DROPOUT_RATES[1])(x)
    outputs = tf.keras.layers.Dense(Config.MOBILENET_OUTPUT_UNITS, activation="sigmoid")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name=Config.MOBILENET_MODEL_NAME)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=Config.MOBILENET_INITIAL_LEARNING_RATE
        ),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def unfreeze_mobilenet_layers(
    model: tf.keras.Model,
    num_layers_to_unfreeze: int = Config.MOBILENET_LAYERS_TO_UNFREEZE,
    fine_tune_lr: float = Config.MOBILENET_FINE_TUNE_LEARNING_RATE,
) -> tf.keras.Model:
    """Unfreeze the requested top MobileNetV2 layers and recompile for fine-tuning.

    Args:
        model: A model returned by :func:`build_mobilenet_model`.
        num_layers_to_unfreeze: Number of trailing backbone layers to make
            trainable. Defaults to ``Config.MOBILENET_LAYERS_TO_UNFREEZE``.
        fine_tune_lr: Positive learning rate for fine-tuning. Defaults to
            ``Config.MOBILENET_FINE_TUNE_LEARNING_RATE``.

    Returns:
        The same model, recompiled with the fine-tuning learning rate.

    Raises:
        ValueError: If the model has no MobileNetV2 base, the layer count is
            outside the base model's bounds, or the learning rate is invalid.
    """
    if (
        not isinstance(num_layers_to_unfreeze, Integral)
        or isinstance(num_layers_to_unfreeze, bool)
    ):
        raise ValueError("num_layers_to_unfreeze must be a non-negative integer.")
    if (
        not isinstance(fine_tune_lr, Real)
        or not math.isfinite(fine_tune_lr)
        or fine_tune_lr <= 0
    ):
        raise ValueError("fine_tune_lr must be a finite positive number.")

    try:
        base_model = model.get_layer(Config.MOBILENET_BASE_MODEL_NAME)
    except ValueError as error:
        raise ValueError("model does not contain the MobileNetV2 base model.") from error

    if not isinstance(base_model, tf.keras.Model):
        raise ValueError("The configured MobileNetV2 base layer is not a Keras model.")
    if not 0 <= num_layers_to_unfreeze <= len(base_model.layers):
        raise ValueError(
            "num_layers_to_unfreeze must not exceed the number of MobileNetV2 layers."
        )

    base_model.trainable = True
    first_trainable_index = len(base_model.layers) - num_layers_to_unfreeze
    for index, layer in enumerate(base_model.layers):
        layer.trainable = index >= first_trainable_index

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=float(fine_tune_lr)),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model