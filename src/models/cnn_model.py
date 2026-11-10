"""Custom convolutional neural network for binary image manipulation detection."""

from __future__ import annotations

from typing import Tuple

import tensorflow as tf

from config import Config


def build_custom_cnn(
    input_shape: Tuple[int, int, int] = Config.INPUT_SHAPE,
) -> tf.keras.Model:
    """Build and compile a four-block custom CNN for binary classification.

    Args:
        input_shape: Input tensor shape in ``(height, width, channels)`` format.
            Defaults to ``Config.INPUT_SHAPE``.

    Returns:
        A compiled Keras model that predicts manipulation probability for a single
        image tensor.

    Raises:
        ValueError: If the input shape is invalid or contains non-positive values.
    """
    if len(input_shape) != 3 or any(dim <= 0 for dim in input_shape):
        raise ValueError("input_shape must be a tuple of three positive integers.")

    inputs = tf.keras.Input(shape=input_shape)

    x = tf.keras.layers.Conv2D(32, (3, 3), padding="same", activation="relu")(inputs)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.MaxPooling2D((2, 2))(x)
    x = tf.keras.layers.SpatialDropout2D(0.2)(x)

    x = tf.keras.layers.Conv2D(64, (3, 3), padding="same", activation="relu")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.MaxPooling2D((2, 2))(x)
    x = tf.keras.layers.SpatialDropout2D(0.2)(x)

    x = tf.keras.layers.Conv2D(128, (3, 3), padding="same", activation="relu")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.MaxPooling2D((2, 2))(x)
    x = tf.keras.layers.SpatialDropout2D(0.25)(x)

    x = tf.keras.layers.Conv2D(256, (3, 3), padding="same", activation="relu")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.MaxPooling2D((2, 2))(x)
    x = tf.keras.layers.SpatialDropout2D(0.25)(x)

    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(
        512,
        activation="relu",
        kernel_regularizer=tf.keras.regularizers.l2(1e-4),
    )(x)
    x = tf.keras.layers.Dropout(0.5)(x)
    x = tf.keras.layers.Dense(256, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="custom_cnn")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ],
    )
    return model
