"""Stage 1 metadata and provenance filter for AI-image detection.

Inspects C2PA content credentials, EXIF/XMP/IPTC metadata, PNG text chunks,
and JPEG comment segments to identify AI-generation signatures before invoking
the heavier Stage 2 ML classifier.

Design rationale
~~~~~~~~~~~~~~~~
Stage 1 is a *high-precision, low-recall* filter.  When metadata clearly names
an AI generator or carries a verified C2PA AI-origin assertion the image can be
classified immediately.  When metadata is absent, stripped, or inconclusive the
image is routed to Stage 2 for ML analysis.

Known limitations (documented inline and surfaced in results)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Absence of metadata proves nothing.  Screenshots, social-media re-uploads,
  WhatsApp/Instagram compression, and format conversion strip metadata.
* Present metadata can be forged or copied onto a real photo.
* Some AI tools (e.g. Google SynthID) embed invisible watermarks that cannot
  be detected through metadata inspection.  This module does not claim to
  detect them.
"""

from __future__ import annotations

import json
import struct
import zlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, Optional

from PIL import ExifTags, Image

from config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceItem:
    """A single piece of metadata evidence supporting the Stage 1 verdict.

    Attributes:
        source: Origin category (c2pa, exif, xmp, iptc, png_chunk, jpeg_comment).
        field_name: The metadata field or chunk key where the signal was found.
        value: Abbreviated value that triggered the match (never raw binary).
        note: Human-readable explanation of why this is relevant.
    """

    source: str
    field_name: str
    value: str
    note: str


@dataclass(frozen=True)
class C2paInfo:
    """Summarize C2PA manifest inspection for the Stage 1 result.

    Attributes:
        present: Whether any C2PA manifest was found in the asset.
        valid: Validation state; True if trusted, False if failed, None if absent.
        signer: Certificate subject or issuer, if extractable.
        claim_generator: ``claim_generator`` string from the active manifest.
    """

    present: bool = False
    valid: Optional[bool] = None
    signer: Optional[str] = None
    claim_generator: Optional[str] = None


@dataclass
class Stage1Result:
    """Output of the Stage 1 metadata and provenance filter.

    Attributes:
        status: One of ``"ai_detected"``, ``"c2pa_present_not_ai"``,
            ``"no_signal"``, or ``"error"``.
        is_ai: ``True`` when AI metadata was found, ``False`` when C2PA is
            present but shows no AI signal, ``None`` when inconclusive.
        confidence: 0.0 to 1.0 expressing metadata certainty.
        generator: Identified AI generator name, or ``None``.
        evidence: Ordered list of evidence items.
        c2pa: C2PA inspection summary.
        route_to_stage2: Whether the ML classifier should still run.
        processing_ms: Wall-clock milliseconds consumed by Stage 1.
    """

    status: str = "no_signal"
    is_ai: Optional[bool] = None
    confidence: float = 0.0
    generator: Optional[str] = None
    evidence: list[EvidenceItem] = field(default_factory=list)
    c2pa: C2paInfo = field(default_factory=C2paInfo)
    route_to_stage2: bool = True
    processing_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dictionary.

        Returns:
            A plain dictionary with nested dataclass fields expanded.
        """
        data = asdict(self)
        return data


# Retained for backward compatibility with the existing app integration.
@dataclass(frozen=True)
class MetadataAssessment:
    """Legacy summary consumed by DetectionService and templates.

    Attributes:
        c2pa_validation_state: Human-readable C2PA validation status.
        has_trusted_ai_claim: Whether a *trusted* C2PA AI assertion was found.
        metadata_clues: Short, user-safe descriptions of metadata findings.
    """

    c2pa_validation_state: str
    has_trusted_ai_claim: bool
    metadata_clues: tuple[str, ...]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def analyze_metadata(image_path: Path) -> Stage1Result:
    """Run all Stage 1 metadata checks on a locally stored image.

    This function never raises.  Any internal exception is caught, logged,
    and the result is returned with ``status="error"`` and
    ``route_to_stage2=True`` so that Stage 2 can still classify the image.

    Args:
        image_path: Absolute or relative path to a validated image file.

    Returns:
        A populated ``Stage1Result`` instance.
    """
    started_at = perf_counter()
    result = Stage1Result()

    try:
        c2pa_info, c2pa_evidence, c2pa_ai_gen = check_c2pa(image_path)
        result.c2pa = c2pa_info
        result.evidence.extend(c2pa_evidence)

        exif_evidence, exif_gen = check_exif_xmp_iptc(image_path)
        result.evidence.extend(exif_evidence)

        chunk_evidence, chunk_gen = check_png_text_chunks(image_path)
        result.evidence.extend(chunk_evidence)

        comment_evidence, comment_gen = check_jpeg_comments(image_path)
        result.evidence.extend(comment_evidence)

        # --- Routing decision ---------------------------------------------------
        _apply_routing(result, c2pa_ai_gen, exif_gen, chunk_gen, comment_gen)

    except Exception as exc:
        logger.error("Stage 1 metadata analysis failed: %s", exc, exc_info=True)
        result.status = "error"
        result.is_ai = None
        result.route_to_stage2 = True

    result.processing_ms = int((perf_counter() - started_at) * 1000)
    return result


def inspect_image_metadata(image_path: Path) -> MetadataAssessment:
    """Legacy wrapper producing the ``MetadataAssessment`` the app expects.

    Delegates to :func:`analyze_metadata` and maps its richer output back to
    the original three-field dataclass so that ``DetectionService`` and
    templates keep working without changes.

    Args:
        image_path: Path to a validated, locally stored image.

    Returns:
        A backward-compatible metadata assessment.
    """
    stage1 = analyze_metadata(image_path)

    # Derive the legacy fields from the Stage 1 result.
    c2pa_state = "not_present"
    if stage1.c2pa.present:
        if stage1.c2pa.valid is True:
            c2pa_state = "Trusted"
        elif stage1.c2pa.valid is False:
            c2pa_state = "unverifiable"
        else:
            c2pa_state = "unknown"

    has_trusted = (
        stage1.c2pa.present
        and stage1.c2pa.valid is True
        and stage1.status == "ai_detected"
        and any(e.source == "c2pa" for e in stage1.evidence)
    )

    clues: list[str] = []
    for ev in stage1.evidence:
        clues.append(ev.note)

    return MetadataAssessment(
        c2pa_validation_state=c2pa_state,
        has_trusted_ai_claim=has_trusted,
        metadata_clues=tuple(sorted(set(clues))),
    )


# ---------------------------------------------------------------------------
# CHECK 1: C2PA Content Credentials
# ---------------------------------------------------------------------------

def check_c2pa(image_path: Path) -> tuple[C2paInfo, list[EvidenceItem], Optional[str]]:
    """Read and interpret the C2PA manifest store from an image file.

    A C2PA manifest alone does **not** mean AI.  Cameras, Photoshop, and
    newsroom tools also sign real photos.  This function only flags AI when
    an explicit ``trainedAlgorithmicMedia`` source type is present, or the
    claim generator / signer matches a known AI tool.

    Args:
        image_path: Path to a locally stored image.

    Returns:
        A tuple of (C2paInfo summary, evidence items, generator name or None).
    """
    try:
        import c2pa
    except ImportError:
        logger.warning("c2pa-python is not installed; skipping C2PA check.")
        return C2paInfo(), [], None

    info = C2paInfo()
    evidence: list[EvidenceItem] = []
    generator: Optional[str] = None

    try:
        # Build optional trust context
        context = _build_c2pa_context(c2pa)

        if context is not None:
            reader = c2pa.Reader.try_create(image_path, context=context)
        else:
            reader = c2pa.Reader.try_create(image_path)

        if reader is None:
            # No C2PA manifest found — this is the common case.
            return C2paInfo(present=False), [], None

        with reader:
            validation_state = reader.get_validation_state() or "unknown"
            manifest = reader.get_active_manifest() or {}

        is_valid = validation_state.casefold() == "trusted"
        claim_gen = manifest.get("claim_generator")
        signer = _extract_signer(manifest)

        info = C2paInfo(
            present=True,
            valid=is_valid,
            signer=signer,
            claim_generator=str(claim_gen) if claim_gen else None,
        )

        # Check for AI-origin digital source type
        has_ai_source = _has_ai_creation_assertion(manifest)
        if has_ai_source:
            evidence.append(EvidenceItem(
                source="c2pa",
                field_name="digitalSourceType",
                value="trainedAlgorithmicMedia",
                note="C2PA manifest declares an AI-origin digital source type.",
            ))

        # Check claim generator / signer against known AI generators
        c2pa_text = _metadata_text(manifest).casefold()
        for marker, product in Config.STAGE1_AI_GENERATOR_MARKERS:
            if marker in c2pa_text:
                evidence.append(EvidenceItem(
                    source="c2pa",
                    field_name="claim_generator",
                    value=product,
                    note=f"C2PA manifest mentions {product}; review its validation state.",
                ))
                generator = product
                break

        if has_ai_source and generator is None:
            generator = "Unknown (C2PA AI-origin)"

        # Validation note
        if info.present and not is_valid:
            evidence.append(EvidenceItem(
                source="c2pa",
                field_name="validation_state",
                value=str(validation_state),
                note=(
                    "C2PA signature validation failed or is unverifiable.  "
                    "The manifest may have been tampered with."
                ),
            ))

    except Exception as exc:
        logger.warning("C2PA inspection encountered an error: %s", exc)
        evidence.append(EvidenceItem(
            source="c2pa",
            field_name="error",
            value=str(exc)[:200],
            note="C2PA metadata could not be read or verified.",
        ))

    return info, evidence, generator


def _build_c2pa_context(c2pa_module: Any) -> Any | None:
    """Build a C2PA trust context from configured trust anchors, if set."""
    anchors_path = Config.C2PA_TRUST_ANCHORS_PATH
    if anchors_path is None:
        return None
    try:
        anchors = anchors_path.read_text(encoding="utf-8")
    except OSError as error:
        logger.warning("Unable to read C2PA trust anchors: %s", error)
        return None

    settings = c2pa_module.Settings.from_dict(
        {
            "verify": {"verify_cert_anchors": True},
            "trust": {"trust_anchors": anchors},
        }
    )
    return c2pa_module.Context(settings)


def _extract_signer(manifest: dict[str, Any]) -> Optional[str]:
    """Extract the certificate subject or issuer from a C2PA manifest."""
    sig_info = manifest.get("signature_info") or {}
    issuer = sig_info.get("issuer")
    if issuer:
        return str(issuer)[:200]
    cert_chain = sig_info.get("cert_chain")
    if isinstance(cert_chain, list) and cert_chain:
        first = cert_chain[0]
        if isinstance(first, dict):
            return str(first.get("subject", first.get("issuer", "")))[:200]
    return None


def _has_ai_creation_assertion(manifest: dict[str, Any]) -> bool:
    """Check C2PA actions assertions for an explicit AI-origin source type.

    Recognized IPTC digital source type vocabulary values:
    - trainedAlgorithmicMedia
    - compositeWithTrainedAlgorithmicMedia
    - algorithmicMedia
    - compositeSynthetic
    """
    assertions = manifest.get("assertions", [])
    if not isinstance(assertions, list):
        return False
    for assertion in assertions:
        if not isinstance(assertion, dict):
            continue
        label = assertion.get("label")
        data = assertion.get("data")
        if not isinstance(label, str) or not label.startswith("c2pa.actions"):
            continue
        if not isinstance(data, dict):
            continue
        actions = data.get("actions", [])
        if not isinstance(actions, list):
            continue
        for action in actions:
            if not isinstance(action, dict):
                continue
            source_type = action.get("digitalSourceType")
            if isinstance(source_type, str):
                normalized = source_type.rsplit("/", 1)[-1].casefold()
                if normalized in Config.STAGE1_AI_SOURCE_TYPES:
                    return True
    return False


# ---------------------------------------------------------------------------
# CHECK 2: EXIF / XMP / IPTC
# ---------------------------------------------------------------------------

def check_exif_xmp_iptc(
    image_path: Path,
) -> tuple[list[EvidenceItem], Optional[str]]:
    """Scan EXIF, XMP, and IPTC metadata for AI generator signatures.

    Uses Pillow's built-in readers.  ExifTool support is optional and can be
    added in the future for broader tag coverage; for now Pillow covers the
    critical fields (Software, ImageDescription, UserComment, XMP).

    Limitations: unsigned EXIF/XMP metadata can be trivially forged.  Findings
    are marked ``(unverified)`` in the evidence notes.

    Args:
        image_path: Path to a locally stored image.

    Returns:
        A tuple of (evidence items, identified generator name or None).
    """
    evidence: list[EvidenceItem] = []
    generator: Optional[str] = None

    try:
        with Image.open(image_path) as image:
            metadata: dict[str, Any] = dict(image.info)

            # Parse XMP if available
            if hasattr(image, "getxmp"):
                try:
                    xmp_data = image.getxmp()
                    if xmp_data:
                        metadata["XMP"] = xmp_data
                except (OSError, SyntaxError, ValueError) as error:
                    logger.debug("Could not parse XMP: %s", error)

            # Parse EXIF tags
            exif_data = image.getexif()
            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                metadata[tag_name] = value
    except (OSError, SyntaxError, Image.DecompressionBombError) as exc:
        logger.debug("Could not read image metadata for EXIF check: %s", exc)
        return evidence, generator

    # First pass: look for IPTC DigitalSourceType (strong signal)
    full_text = _metadata_text(metadata).casefold()
    for ai_source in Config.STAGE1_AI_SOURCE_TYPES:
        if ai_source in full_text:
            evidence.append(EvidenceItem(
                source="iptc",
                field_name="DigitalSourceType",
                value=ai_source,
                note=f"IPTC DigitalSourceType contains '{ai_source}' (strong AI signal, unverified).",
            ))
            generator = "Unknown (IPTC AI source type)"
            break

    # Second pass: keyword matching against known AI generators
    for key, value in metadata.items():
        key_text = str(key).casefold()
        value_text = _metadata_text(value).casefold()

        # Check for diffusion-style parameters chunk (may appear as EXIF too)
        if "parameters" in key_text:
            for sd_marker in Config.STAGE1_SD_PARAMETER_MARKERS:
                if sd_marker in value_text:
                    evidence.append(EvidenceItem(
                        source="exif",
                        field_name=str(key),
                        value=value_text[:120],
                        note="Diffusion-style generation parameters found in metadata (unverified).",
                    ))
                    if generator is None:
                        generator = "Stable Diffusion"
                    break

        # Check known generator names
        for marker, product in Config.STAGE1_AI_GENERATOR_MARKERS:
            if marker in key_text or marker in value_text:
                evidence.append(EvidenceItem(
                    source="exif" if key_text in Config.STAGE1_EXIF_FIELDS else "xmp",
                    field_name=str(key),
                    value=value_text[:120],
                    note=f"Metadata mentions {product} (unverified).",
                ))
                if generator is None:
                    generator = product
                break  # One match per key is enough.

    return evidence, generator


# ---------------------------------------------------------------------------
# CHECK 3a: PNG text chunks
# ---------------------------------------------------------------------------

def check_png_text_chunks(
    image_path: Path,
) -> tuple[list[EvidenceItem], Optional[str]]:
    """Scan PNG tEXt, iTXt, and zTXt chunks for AI generation metadata.

    Detects:
    * AUTOMATIC1111 / SD.Next / Forge:  ``parameters`` chunk with
      "Steps:", "Sampler:", "CFG scale:", "Seed:", "Model hash:"
    * ComfyUI:  ``prompt`` and ``workflow`` chunks with JSON containing
      "class_type" and "KSampler" nodes
    * InvokeAI:  ``invokeai_metadata``, ``sd-metadata`` chunk keys
    * NovelAI:  ``Software`` = "NovelAI" and ``Comment`` JSON with prompt
    * Generic:  Any chunk with JSON containing "prompt" + "seed" + "sampler"

    JSON is parsed with ``json.loads`` inside a try/except.  Nothing from the
    metadata is ever executed.

    Args:
        image_path: Path to a locally stored image.

    Returns:
        A tuple of (evidence items, identified generator name or None).
    """
    evidence: list[EvidenceItem] = []
    generator: Optional[str] = None

    # Quick format check: only PNG has text chunks
    try:
        with open(image_path, "rb") as fh:
            header = fh.read(8)
        if header != Config.MAGIC_BYTES.get("png", b"\x89PNG\r\n\x1a\n"):
            return evidence, generator
    except OSError:
        return evidence, generator

    # Read PNG metadata via Pillow's .info dict
    try:
        with Image.open(image_path) as image:
            info = dict(image.info)
    except (OSError, SyntaxError, Image.DecompressionBombError):
        return evidence, generator

    # Also try reading raw PNG chunks for keys Pillow may skip
    raw_chunks = _read_png_text_chunks_raw(image_path)
    for key, value in raw_chunks.items():
        if key not in info:
            info[key] = value

    # --- AUTOMATIC1111 / SD.Next / Forge ---
    params_text = str(info.get("parameters", ""))
    if params_text:
        matched_markers = [
            m for m in Config.STAGE1_SD_PARAMETER_MARKERS
            if m in params_text.casefold()
        ]
        if len(matched_markers) >= 2:
            evidence.append(EvidenceItem(
                source="png_chunk",
                field_name="parameters",
                value=params_text[:160],
                note="Stable Diffusion AUTOMATIC1111/Forge-style generation parameters found.",
            ))
            if generator is None:
                generator = "Stable Diffusion (AUTOMATIC1111)"

    # --- ComfyUI ---
    for key in ("prompt", "workflow"):
        chunk_val = info.get(key)
        if not isinstance(chunk_val, str) or not chunk_val.strip():
            continue
        try:
            parsed = json.loads(chunk_val)
        except (json.JSONDecodeError, ValueError):
            continue
        chunk_text = str(parsed).casefold()
        if "class_type" in chunk_text or "ksampler" in chunk_text:
            evidence.append(EvidenceItem(
                source="png_chunk",
                field_name=key,
                value=f"JSON with class_type/KSampler ({len(chunk_val)} bytes)",
                note="ComfyUI workflow or prompt metadata found.",
            ))
            if generator is None:
                generator = "ComfyUI"

    # --- InvokeAI ---
    for key in ("invokeai_metadata", "sd-metadata", "invokeai"):
        if key in info:
            evidence.append(EvidenceItem(
                source="png_chunk",
                field_name=key,
                value=str(info[key])[:120],
                note="InvokeAI generation metadata found.",
            ))
            if generator is None:
                generator = "InvokeAI"

    # --- NovelAI ---
    software_val = str(info.get("Software", "")).casefold()
    if "novelai" in software_val:
        evidence.append(EvidenceItem(
            source="png_chunk",
            field_name="Software",
            value=str(info.get("Software", "")),
            note="NovelAI software tag found.",
        ))
        if generator is None:
            generator = "NovelAI"
    comment_val = info.get("Comment")
    if isinstance(comment_val, str) and comment_val.strip().startswith("{"):
        try:
            comment_parsed = json.loads(comment_val)
            if isinstance(comment_parsed, dict) and (
                "prompt" in comment_parsed or "seed" in comment_parsed
            ):
                evidence.append(EvidenceItem(
                    source="png_chunk",
                    field_name="Comment",
                    value=f"JSON with prompt/seed keys ({len(comment_val)} bytes)",
                    note="Structured generation metadata found in Comment chunk.",
                ))
                if generator is None and "novelai" in software_val:
                    generator = "NovelAI"
                elif generator is None:
                    generator = "Unknown (generation metadata)"
        except (json.JSONDecodeError, ValueError):
            pass

    # --- Generic JSON with prompt+seed+sampler ---
    if generator is None:
        for key, value in info.items():
            if not isinstance(value, str) or len(value) < 10:
                continue
            try:
                parsed = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(parsed, dict):
                keys_lower = {k.casefold() for k in parsed}
                if {"prompt", "seed", "sampler"} <= keys_lower:
                    evidence.append(EvidenceItem(
                        source="png_chunk",
                        field_name=str(key),
                        value=f"JSON with prompt+seed+sampler ({len(value)} bytes)",
                        note="Generation metadata matching prompt/seed/sampler pattern found.",
                    ))
                    generator = "Unknown (generation metadata)"

    # --- Check all chunk values against known generator names ---
    for key, value in info.items():
        val_text = str(value).casefold()
        for marker, product in Config.STAGE1_AI_GENERATOR_MARKERS:
            if marker in val_text and not any(
                e.field_name == str(key) and product in e.note
                for e in evidence
            ):
                evidence.append(EvidenceItem(
                    source="png_chunk",
                    field_name=str(key),
                    value=val_text[:120],
                    note=f"PNG chunk mentions {product} (unverified).",
                ))
                if generator is None:
                    generator = product
                break

    return evidence, generator


def _read_png_text_chunks_raw(image_path: Path) -> dict[str, str]:
    """Read tEXt, iTXt, and zTXt chunks directly from a PNG file.

    Pillow sometimes skips certain chunk keys.  This low-level reader catches
    them without decoding pixel data.

    Args:
        image_path: Path to a PNG image file.

    Returns:
        A dictionary mapping chunk keyword to decoded text value.
    """
    chunks: dict[str, str] = {}
    try:
        with open(image_path, "rb") as fh:
            signature = fh.read(8)
            if signature != b"\x89PNG\r\n\x1a\n":
                return chunks

            while True:
                length_bytes = fh.read(4)
                if len(length_bytes) < 4:
                    break
                length = struct.unpack(">I", length_bytes)[0]
                chunk_type = fh.read(4)
                if len(chunk_type) < 4:
                    break
                data = fh.read(length)
                _crc = fh.read(4)

                type_str = chunk_type.decode("ascii", errors="replace")

                if type_str == "tEXt" and b"\x00" in data:
                    key, _, value = data.partition(b"\x00")
                    chunks[key.decode("latin-1", errors="replace")] = (
                        value.decode("latin-1", errors="replace")
                    )
                elif type_str == "zTXt" and b"\x00" in data:
                    key, _, rest = data.partition(b"\x00")
                    if len(rest) > 1:
                        try:
                            decompressed = zlib.decompress(rest[1:])
                            chunks[key.decode("latin-1", errors="replace")] = (
                                decompressed.decode("utf-8", errors="replace")
                            )
                        except zlib.error:
                            pass
                elif type_str == "iTXt" and b"\x00" in data:
                    key, _, rest = data.partition(b"\x00")
                    # iTXt: compression_flag, compression_method, language, translated_keyword, text
                    parts = rest.split(b"\x00", 3)
                    if len(parts) >= 4:
                        text_data = parts[3]
                        comp_flag = parts[0][0:1]
                        if comp_flag == b"\x01":
                            try:
                                text_data = zlib.decompress(text_data)
                            except zlib.error:
                                pass
                        chunks[key.decode("utf-8", errors="replace")] = (
                            text_data.decode("utf-8", errors="replace")
                        )
                elif type_str == "IEND":
                    break

                # Safety: stop after reading too many bytes of metadata
                if fh.tell() > Config.STAGE1_MAX_METADATA_BYTES:
                    break

    except (OSError, struct.error) as exc:
        logger.debug("Raw PNG chunk reading failed: %s", exc)

    return chunks


# ---------------------------------------------------------------------------
# CHECK 3b: JPEG comments
# ---------------------------------------------------------------------------

def check_jpeg_comments(
    image_path: Path,
) -> tuple[list[EvidenceItem], Optional[str]]:
    """Scan the JPEG COM (comment) segment for AI generation signatures.

    Args:
        image_path: Path to a locally stored image.

    Returns:
        A tuple of (evidence items, identified generator name or None).
    """
    evidence: list[EvidenceItem] = []
    generator: Optional[str] = None

    try:
        with open(image_path, "rb") as fh:
            header = fh.read(3)
        if header != Config.MAGIC_BYTES.get("jpeg", b"\xff\xd8\xff"):
            return evidence, generator
    except OSError:
        return evidence, generator

    comments = _read_jpeg_comments(image_path)
    for comment_text in comments:
        lower = comment_text.casefold()

        # Check known generators
        for marker, product in Config.STAGE1_AI_GENERATOR_MARKERS:
            if marker in lower:
                evidence.append(EvidenceItem(
                    source="jpeg_comment",
                    field_name="COM",
                    value=comment_text[:120],
                    note=f"JPEG comment mentions {product} (unverified).",
                ))
                if generator is None:
                    generator = product
                break

        # Check for JSON with prompt/seed
        if comment_text.strip().startswith("{"):
            try:
                parsed = json.loads(comment_text)
                if isinstance(parsed, dict):
                    keys_lower = {k.casefold() for k in parsed}
                    if "prompt" in keys_lower:
                        evidence.append(EvidenceItem(
                            source="jpeg_comment",
                            field_name="COM",
                            value=f"JSON with prompt key ({len(comment_text)} bytes)",
                            note="Structured generation metadata found in JPEG comment.",
                        ))
                        if generator is None:
                            generator = "Unknown (generation metadata)"
            except (json.JSONDecodeError, ValueError):
                pass

    return evidence, generator


def _read_jpeg_comments(image_path: Path) -> list[str]:
    """Extract JPEG COM segments from a file without full image decoding.

    Args:
        image_path: Path to a JPEG image file.

    Returns:
        A list of decoded comment strings.
    """
    comments: list[str] = []
    try:
        with open(image_path, "rb") as fh:
            if fh.read(2) != b"\xff\xd8":
                return comments

            while True:
                marker = fh.read(2)
                if len(marker) < 2:
                    break
                if marker[0:1] != b"\xff":
                    break

                marker_type = marker[1]

                # SOS (Start of Scan) or EOI (End of Image) — stop scanning
                if marker_type in (0xDA, 0xD9):
                    break

                # Standalone markers (RST, TEM, padding)
                if marker_type in range(0xD0, 0xDA) or marker_type == 0x01:
                    continue

                # Read segment length
                length_bytes = fh.read(2)
                if len(length_bytes) < 2:
                    break
                seg_length = struct.unpack(">H", length_bytes)[0]
                if seg_length < 2:
                    break
                payload = fh.read(seg_length - 2)

                # COM marker = 0xFE
                if marker_type == 0xFE:
                    text = payload.decode("utf-8", errors="replace").strip()
                    if text:
                        comments.append(text)

                # Safety limit
                if fh.tell() > Config.STAGE1_MAX_METADATA_BYTES:
                    break

    except (OSError, struct.error) as exc:
        logger.debug("JPEG comment extraction failed: %s", exc)

    return comments


# ---------------------------------------------------------------------------
# Routing decision
# ---------------------------------------------------------------------------

def _apply_routing(
    result: Stage1Result,
    c2pa_gen: Optional[str],
    exif_gen: Optional[str],
    chunk_gen: Optional[str],
    comment_gen: Optional[str],
) -> None:
    """Determine the status, confidence, and routing from collected evidence.

    Routing rules:
    * Valid C2PA + AI signal → ai_detected, 0.99, skip Stage 2
    * Invalid C2PA + AI signal → ai_detected, 0.85, skip Stage 2
    * Strong generator chunk or IPTC DigitalSourceType → ai_detected, 0.95, skip Stage 2
    * Weak keyword match → ai_detected, 0.75, still route to Stage 2
    * C2PA present but no AI signal → c2pa_present_not_ai, route to Stage 2
    * No signal → no_signal, route to Stage 2
    """
    # Pick the best generator name (priority: C2PA > chunk > EXIF > comment)
    best_gen = c2pa_gen or chunk_gen or exif_gen or comment_gen

    has_c2pa_ai = c2pa_gen is not None or any(
        e.source == "c2pa" and "AI-origin" in e.note for e in result.evidence
    )
    has_strong_chunk = chunk_gen is not None and any(
        e.source == "png_chunk" and (
            "generation parameters" in e.note.casefold()
            or "workflow" in e.note.casefold()
            or "invokeai" in e.note.casefold()
            or "novelai" in e.note.casefold()
        )
        for e in result.evidence
    )
    has_iptc_source = any(
        e.source == "iptc" for e in result.evidence
    )
    has_weak_keyword = (exif_gen is not None or comment_gen is not None) and not has_c2pa_ai

    if has_c2pa_ai:
        result.status = "ai_detected"
        result.is_ai = True
        result.generator = best_gen
        if result.c2pa.valid is True:
            result.confidence = 0.99
            result.route_to_stage2 = False
        else:
            result.confidence = 0.85
            result.route_to_stage2 = False
    elif has_strong_chunk or has_iptc_source:
        result.status = "ai_detected"
        result.is_ai = True
        result.confidence = 0.95
        result.generator = best_gen
        result.route_to_stage2 = False
    elif has_weak_keyword:
        result.status = "ai_detected"
        result.is_ai = True
        result.confidence = 0.75
        result.generator = best_gen
        result.route_to_stage2 = True  # Let Stage 2 confirm
    elif result.c2pa.present:
        result.status = "c2pa_present_not_ai"
        result.is_ai = False
        result.confidence = 0.0
        result.route_to_stage2 = True
    else:
        result.status = "no_signal"
        result.is_ai = None
        result.confidence = 0.0
        result.route_to_stage2 = True


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _metadata_text(value: Any) -> str:
    """Flatten structured metadata into a bounded string for marker matching.

    Args:
        value: Any metadata value (dict, list, bytes, str, etc.).

    Returns:
        A space-joined string of all leaf text values, truncated to
        ``Config.METADATA_VALUE_SCAN_LIMIT`` characters.
    """
    parts: list[str] = []
    pending = [value]
    length = 0
    limit = Config.METADATA_VALUE_SCAN_LIMIT
    while pending and length < limit:
        current = pending.pop()
        if isinstance(current, dict):
            pending.extend(reversed(list(current.items())))
            continue
        elif isinstance(current, (list, tuple)):
            pending.extend(reversed(current))
            continue
        elif isinstance(current, bytes):
            text = current.decode("utf-8", errors="replace")
        elif isinstance(current, str):
            text = current
        else:
            continue
        text = text[: limit - length]
        parts.append(text)
        length += len(text)
    return " ".join(parts)
