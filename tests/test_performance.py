"""Latency-profile tests for the synchronous image analysis endpoint."""

from __future__ import annotations

from io import BytesIO
from time import perf_counter

from flask import Flask

from config import Config


def test_cpu_analysis_average_latency_is_within_budget(
    app: Flask,
    synthetic_jpeg_bytes: bytes,
) -> None:
    """Measure repeated CPU-only analysis requests against the latency budget.

    The application fixture registers the lightweight CPU fallback model, so
    this profile covers upload validation, preprocessing, inference dispatch,
    ELA generation, and response construction without trained model files.

    Args:
        app: Isolated Flask application fixture.
        synthetic_jpeg_bytes: In-memory JPEG used for each request.
    """
    durations: list[float] = []

    for _ in range(Config.PERFORMANCE_TEST_ITERATIONS):
        with app.test_client() as client:
            started_at = perf_counter()
            response = client.post(
                "/analyze",
                data={"image": (BytesIO(synthetic_jpeg_bytes), "performance.jpg")},
                content_type="multipart/form-data",
                headers={"Accept": "application/json"},
            )
            durations.append(perf_counter() - started_at)

            assert response.status_code == 200
            result = response.get_json()
            assert result is not None
            report_response = client.get(f"/report/{result['session_id']}")
            assert report_response.status_code == 200
            assert report_response.mimetype == "application/pdf"

    average_duration = sum(durations) / len(durations)
    assert average_duration < Config.MAX_ANALYSIS_LATENCY_SECONDS, (
        f"Average /analyze latency was {average_duration:.3f}s across "
        f"{Config.PERFORMANCE_TEST_ITERATIONS} CPU-only requests; "
        f"budget is {Config.MAX_ANALYSIS_LATENCY_SECONDS:.3f}s."
    )
