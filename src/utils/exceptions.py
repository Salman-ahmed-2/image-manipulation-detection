"""Domain-specific exceptions shared across application layers."""

from __future__ import annotations


class AppError(Exception):
    """Base class for expected application-level failures."""


class ValidationError(AppError):
    """Raised when an uploaded file fails validation."""


class PayloadTooLargeError(ValidationError):
    """Raised when an upload exceeds the configured request-size limit."""


class CorruptImageError(ValidationError):
    """Raised when image bytes cannot be identified or decoded safely."""


class ModelInferenceError(AppError):
    """Raised when model prediction cannot complete successfully."""


class ModelNotLoadedError(ModelInferenceError):
    """Raised when a requested model is not available in memory."""


class ReportGenerationError(AppError):
    """Raised when an analysis report cannot be generated."""
