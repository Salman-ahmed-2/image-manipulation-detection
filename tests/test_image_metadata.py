"""Tests for Stage 1 metadata/provenance filter and backward-compatible helpers."""

from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin

from config import Config
from src.services.report_service import ReportService
from src.utils import image_metadata
from src.utils.image_metadata import (
    C2paInfo,
    EvidenceItem,
    analyze_metadata,
    check_c2pa,
    check_exif_xmp_iptc,
    check_jpeg_comments,
    check_png_text_chunks,
    inspect_image_metadata,
)


def _write_png(path: Path, chunks: dict[str, str] | None = None) -> None:
    """Write a synthetic PNG with optional textual metadata chunks."""
    metadata = PngImagePlugin.PngInfo()
    for key, value in (
        chunks
        if chunks is not None
        else {"parameters": "Steps: 20; CFG scale: 7", "Software": "ComfyUI"}
    ).items():
        metadata.add_text(key, value)
    Image.new("RGB", (8, 8), color=(40, 80, 120)).save(path, pnginfo=metadata)


def _write_jpeg_with_comment(path: Path, comment: str) -> None:
    """Write a synthetic JPEG containing a COM (0xFE) comment segment."""
    base = path.with_suffix(".tmp.jpg")
    Image.new("RGB", (8, 8), color=(40, 80, 120)).save(base, format="JPEG")
    raw = base.read_bytes()
    base.unlink()
    payload = comment.encode("utf-8")
    com_segment = b"\xff\xfe" + struct.pack(">H", len(payload) + 2) + payload
    # Insert COM right after SOI (0xFFD8)
    path.write_bytes(raw[:2] + com_segment + raw[2:])


def test_inspect_image_metadata_reports_unverified_png_clues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PNG metadata clues are reported via the legacy wrapper without C2PA trust."""
    image_path = tmp_path / "synthetic.png"
    _write_png(image_path)
    monkeypatch.setattr(
        image_metadata,
        "check_c2pa",
        lambda path: (C2paInfo(present=False), [], None),
    )

    assessment = inspect_image_metadata(image_path)

    assert assessment.c2pa_validation_state == "not_present"
    assert assessment.has_trusted_ai_claim is False
    assert any("AUTOMATIC1111" in clue for clue in assessment.metadata_clues)
    assert any("ComfyUI" in clue for clue in assessment.metadata_clues)


def test_inspect_image_metadata_reads_nested_xmp_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Generator names nested in parsed XMP are found, not silently skipped."""
    image_path = tmp_path / "synthetic.jpg"
    Image.new("RGB", (8, 8), color=(40, 80, 120)).save(image_path)
    monkeypatch.setattr(
        Image.Image,
        "getxmp",
        lambda image: {"xmpmeta": {"Description": {"CreatorTool": "Google Gemini"}}},
    )

    evidence, generator = check_exif_xmp_iptc(image_path)

    assert generator == "Google Gemini"
    assert any("Google Gemini (unverified)." in item.note for item in evidence)


def test_c2pa_reader_handles_image_without_credentials(tmp_path: Path) -> None:
    """The official C2PA reader recognizes an ordinary image without credentials."""
    image_path = tmp_path / "plain.jpg"
    Image.new("RGB", (8, 8), color=(40, 80, 120)).save(image_path)

    info, evidence, generator = check_c2pa(image_path)

    assert info.present is False
    assert info.valid is None
    assert evidence == []
    assert generator is None


def test_only_trusted_c2pa_ai_claim_is_authoritative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid but untrusted C2PA claim does not set has_trusted_ai_claim."""
    image_path = tmp_path / "synthetic.png"
    _write_png(image_path)
    monkeypatch.setattr(
        image_metadata,
        "check_c2pa",
        lambda path: (
            C2paInfo(present=True, valid=False, claim_generator="DALL-E"),
            [
                EvidenceItem(
                    source="c2pa",
                    field_name="digitalSourceType",
                    value="trainedAlgorithmicMedia",
                    note="C2PA manifest declares an AI-origin digital source type.",
                )
            ],
            "DALL-E",
        ),
    )

    assessment = inspect_image_metadata(image_path)

    assert assessment.c2pa_validation_state == "unverifiable"
    assert assessment.has_trusted_ai_claim is False


def test_trusted_c2pa_ai_claim_is_authoritative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A trusted C2PA claim can be selected for the provenance-only route."""
    image_path = tmp_path / "synthetic.png"
    _write_png(image_path)
    monkeypatch.setattr(
        image_metadata,
        "check_c2pa",
        lambda path: (
            C2paInfo(present=True, valid=True, claim_generator="OpenAI"),
            [
                EvidenceItem(
                    source="c2pa",
                    field_name="digitalSourceType",
                    value="trainedAlgorithmicMedia",
                    note="C2PA manifest declares an AI-origin digital source type.",
                )
            ],
            "OpenAI",
        ),
    )

    assessment = inspect_image_metadata(image_path)

    assert assessment.c2pa_validation_state == "Trusted"
    assert assessment.has_trusted_ai_claim is True


def test_ai_creation_assertion_requires_a_standard_source_type() -> None:
    """Unrelated C2PA actions are not mistaken for AI-origin claims."""
    manifest = {
        "assertions": [
            {
                "label": "c2pa.actions.v2",
                "data": {
                    "actions": [
                        {
                            "action": "c2pa.created",
                            "digitalSourceType": (
                                "http://cv.iptc.org/newscodes/digitalsourcetype/"
                                "trainedAlgorithmicMedia"
                            ),
                        }
                    ]
                },
            }
        ]
    }

    assert image_metadata._has_ai_creation_assertion(manifest) is True
    assert image_metadata._has_ai_creation_assertion(
        {"assertions": [{"label": "c2pa.actions", "data": {"actions": []}}]}
    ) is False


# ---------------------------------------------------------------------------
# 7 core Stage 1 fixture scenarios
# ---------------------------------------------------------------------------


def test_stage1_scenario1_trusted_c2pa_ai_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario 1: Trusted C2PA AI image returns 0.99 confidence and skips Stage 2."""
    image_path = tmp_path / "c2pa_ai.jpg"
    Image.new("RGB", (8, 8), color=(40, 80, 120)).save(image_path)

    manifest = {
        "claim_generator": "OpenAI DALL-E 3",
        "signature_info": {"issuer": "OpenAI"},
        "assertions": [
            {
                "label": "c2pa.actions.v2",
                "data": {
                    "actions": [
                        {
                            "action": "c2pa.created",
                            "digitalSourceType": (
                                "http://cv.iptc.org/newscodes/digitalsourcetype/"
                                "trainedAlgorithmicMedia"
                            ),
                        }
                    ]
                },
            }
        ],
    }

    class FakeReader:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get_validation_state(self):
            return "Trusted"

        def get_active_manifest(self):
            return manifest

    class FakeC2pa:
        class Reader:
            @staticmethod
            def try_create(*args, **kwargs):
                return FakeReader()

    import sys

    monkeypatch.setitem(sys.modules, "c2pa", FakeC2pa)

    result = analyze_metadata(image_path)

    assert result.status == "ai_detected"
    assert result.is_ai is True
    assert result.confidence == 0.99
    assert result.route_to_stage2 is False
    assert result.c2pa.present is True
    assert result.c2pa.valid is True
    assert result.c2pa.signer == "OpenAI"
    assert result.generator in ("DALL-E", "OpenAI")
    assert any(e.source == "c2pa" for e in result.evidence)


def test_stage1_scenario2_stable_diffusion_png_parameters(tmp_path: Path) -> None:
    """Scenario 2: AUTOMATIC1111 PNG parameters chunk skips Stage 2 with 0.95 confidence."""
    image_path = tmp_path / "sd_output.png"
    _write_png(
        image_path,
        {
            "parameters": (
                "a cozy studio\nSteps: 28, Sampler: Euler a, CFG scale: 7.5, Seed: 42"
            )
        },
    )

    result = analyze_metadata(image_path)

    assert result.status == "ai_detected"
    assert result.is_ai is True
    assert result.confidence == 0.95
    assert result.route_to_stage2 is False
    assert result.generator == "Stable Diffusion (AUTOMATIC1111)"
    assert any(e.source == "png_chunk" and e.field_name == "parameters" for e in result.evidence)


def test_stage1_scenario3_comfyui_png_workflow_json(tmp_path: Path) -> None:
    """Scenario 3: ComfyUI prompt JSON chunk skips Stage 2 with 0.95 confidence."""
    image_path = tmp_path / "comfy_output.png"
    workflow_json = json.dumps({"3": {"class_type": "KSampler", "inputs": {"seed": 1}}})
    _write_png(image_path, {"prompt": workflow_json})

    result = analyze_metadata(image_path)

    assert result.status == "ai_detected"
    assert result.is_ai is True
    assert result.confidence == 0.95
    assert result.route_to_stage2 is False
    assert result.generator == "ComfyUI"
    assert any(e.source == "png_chunk" and e.field_name == "prompt" for e in result.evidence)


def test_stage1_scenario4_normal_camera_jpeg_with_exif(tmp_path: Path) -> None:
    """Scenario 4: Normal camera JPEG with EXIF is NOT flagged as AI and routes to Stage 2."""
    image_path = tmp_path / "camera.jpg"
    img = Image.new("RGB", (8, 8), color=(40, 80, 120))
    exif = img.getexif()
    exif[271] = "Canon"  # Make
    exif[272] = "Canon EOS R5"  # Model
    exif[305] = "Adobe Lightroom"  # Software
    img.save(image_path, format="JPEG", exif=exif)

    result = analyze_metadata(image_path)

    assert result.status == "no_signal"
    assert result.is_ai is None
    assert result.confidence == 0.0
    assert result.route_to_stage2 is True
    assert result.generator is None


def test_stage1_scenario5_stripped_screenshot_png(tmp_path: Path) -> None:
    """Scenario 5: Stripped PNG without metadata returns no_signal and routes to Stage 2."""
    image_path = tmp_path / "screenshot.png"
    _write_png(image_path, {})

    result = analyze_metadata(image_path)

    assert result.status == "no_signal"
    assert result.is_ai is None
    assert result.confidence == 0.0
    assert result.route_to_stage2 is True
    assert result.evidence == []


def test_stage1_scenario6_corrupt_file_fails_open(tmp_path: Path) -> None:
    """Scenario 6: Corrupt/truncated file never crashes and routes to Stage 2."""
    image_path = tmp_path / "corrupt.jpg"
    image_path.write_bytes(b"\xff\xd8\xff\xe0\x00\x10truncated-garbage")

    result = analyze_metadata(image_path)

    assert result.route_to_stage2 is True
    assert result.status in ("no_signal", "error")


def test_stage1_scenario6b_internal_exception_returns_error_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unexpected Stage 1 exception is caught and fails open to Stage 2."""
    image_path = tmp_path / "plain.png"
    _write_png(image_path, {})
    monkeypatch.setattr(
        image_metadata,
        "check_c2pa",
        lambda path: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = analyze_metadata(image_path)

    assert result.status == "error"
    assert result.is_ai is None
    assert result.route_to_stage2 is True


def test_stage1_scenario7_photoshop_c2pa_without_ai_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario 7: Trusted C2PA from Photoshop without AI action returns c2pa_present_not_ai."""
    image_path = tmp_path / "photoshop_edit.jpg"
    Image.new("RGB", (8, 8), color=(40, 80, 120)).save(image_path)

    manifest = {
        "claim_generator": "Adobe Photoshop 25.0",
        "signature_info": {"issuer": "Adobe Inc."},
        "assertions": [
            {
                "label": "c2pa.actions.v2",
                "data": {"actions": [{"action": "c2pa.edited"}]},
            }
        ],
    }

    class FakeReader:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get_validation_state(self):
            return "Trusted"

        def get_active_manifest(self):
            return manifest

    class FakeC2pa:
        class Reader:
            @staticmethod
            def try_create(*args, **kwargs):
                return FakeReader()

    import sys

    monkeypatch.setitem(sys.modules, "c2pa", FakeC2pa)

    result = analyze_metadata(image_path)

    assert result.status == "c2pa_present_not_ai"
    assert result.is_ai is False
    assert result.route_to_stage2 is True
    assert result.c2pa.present is True
    assert result.c2pa.valid is True


def test_jpeg_comment_segment_detects_weak_generator_signal(tmp_path: Path) -> None:
    """JPEG COM comment mentioning Midjourney yields weak signal (0.75, routes to Stage 2)."""
    image_path = tmp_path / "commented.jpg"
    _write_jpeg_with_comment(image_path, "Generated with Midjourney v6")

    evidence, generator = check_jpeg_comments(image_path)
    assert generator == "Midjourney"
    assert any(e.source == "jpeg_comment" for e in evidence)

    result = analyze_metadata(image_path)
    assert result.status == "ai_detected"
    assert result.confidence == 0.75
    assert result.route_to_stage2 is True


def test_png_chunks_detect_invokeai_and_novelai(tmp_path: Path) -> None:
    """InvokeAI and NovelAI PNG chunks are detected cleanly."""
    invoke_path = tmp_path / "invoke.png"
    _write_png(invoke_path, {"invokeai_metadata": '{"model": "sdxl"}'})
    ev1, gen1 = check_png_text_chunks(invoke_path)
    assert gen1 == "InvokeAI"
    assert any(e.field_name == "invokeai_metadata" for e in ev1)

    novel_path = tmp_path / "novel.png"
    _write_png(
        novel_path,
        {"Software": "NovelAI", "Comment": '{"prompt": "sky", "seed": 99}'},
    )
    ev2, gen2 = check_png_text_chunks(novel_path)
    assert gen2 == "NovelAI"
    assert any(e.field_name == "Software" for e in ev2)


def test_pdf_report_supports_provenance_without_model_score(tmp_path: Path) -> None:
    """Generate a valid PDF for a metadata result that has no model probability."""
    image_path = tmp_path / "synthetic.png"
    Image.new("RGB", (8, 8), color=(40, 80, 120)).save(image_path)
    result = {
        "verdict_label": "AI-generated",
        "verdict_code": 1,
        "raw_probability": None,
        "model_used": None,
        "model_display_name": "Trusted C2PA Content Credentials",
        "preprocessing_description": "Trusted AI-origin assertion; ML inference skipped",
        "score_type": None,
        "classification_source": "verified_c2pa",
        "metadata_assessment": {
            "c2pa_validation_state": "Trusted",
            "has_trusted_ai_claim": True,
            "metadata_clues": [],
        },
        "disclaimer": Config.C2PA_PROVENANCE_NOTICE,
    }

    pdf = ReportService.generate_pdf_report(result, image_path)

    assert pdf.startswith(b"%PDF")
