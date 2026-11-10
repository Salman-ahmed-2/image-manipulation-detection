"""Domain exception hierarchy for the Image Manipulation Detection System."""

from __future__ import annotations


class AppError(Exception):
    """Base application exception for all domain errors."""

    def __init__(self, message: str = "An unexpected error occurred.") -> None:
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    """Raised when an uploaded file or input parameter fails validation."""


class PayloadTooLargeError(ValidationError):
    """Raised when an uploaded payload exceeds the maximum permitted size."""


class CorruptImageError(ValidationError):
    """Raised when an image file is corrupted, truncated, or unidentifiable."""


class ModelInferenceError(AppError):
    """Raised when an error occurs during model prediction or forward pass."""


class ModelNotLoadedError(ModelInferenceError):
    """Raised when a requested model is not loaded in memory."""


class ReportGenerationError(AppError):
    """Raised when PDF forensic report compilation fails."""
