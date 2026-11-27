"""Inference adapter for Hugging Face image-classification models."""

from __future__ import annotations

from typing import Any

from PIL import Image

from config import Config


class HuggingFaceImageClassifier:
    """Run a Transformers image classifier on a Pillow RGB image."""

    def __init__(self, model: Any, image_processor: Any) -> None:
        """Store the loaded model and resolve the FAKE class index.

        Args:
            model: Loaded Transformers image-classification model.
            image_processor: Processor loaded from the same model revision.

        Raises:
            ValueError: If the model config does not define a FAKE class.
        """
        labels = {
            int(label_id): str(label_name).strip().upper()
            for label_id, label_name in model.config.id2label.items()
        }
        fake_ids = [label_id for label_id, label_name in labels.items() if label_name == "FAKE"]
        if len(fake_ids) != 1:
            raise ValueError(
                f"Hugging Face model must define exactly one FAKE label; found {labels}."
            )

        self._model = model.to("cpu")
        self._model.eval()
        self._image_processor = image_processor
        self._fake_class_id = fake_ids[0]

    def predict_image(self, image: Image.Image) -> float:
        """Return the model's softmax score for the FAKE (AI-generated) class.

        Args:
            image: Source image; it is converted to RGB before processor handling.

        Returns:
            Softmax probability for the FAKE class.

        Raises:
            TypeError: If image is not a Pillow image.
        """
        if not isinstance(image, Image.Image):
            raise TypeError("image must be a PIL Image.")

        import torch

        inputs = self._image_processor(images=image.convert("RGB"), return_tensors="pt")
        with torch.inference_mode():
            logits = self._model(**inputs).logits
            probabilities = torch.softmax(logits, dim=-1)
        return float(probabilities[0, self._fake_class_id].item())
