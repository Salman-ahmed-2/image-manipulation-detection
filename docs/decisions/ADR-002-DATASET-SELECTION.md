# ADR-002: Dataset Selection (CASIA v2.0 Primary & CASIA v1.0 Secondary)

## Context & Problem Statement
Training and evaluating deep learning models for image tampering detection requires benchmark photographic collections featuring realistic, annotated digital manipulations (specifically copy-move cloning and image splicing) alongside authentic pristine counterparts.

## Considered Options
1. **CASIA v2.0 (Primary) + CASIA v1.0 (Secondary)** (Selected)
2. **Columbia Splicing Dataset** (Rejected: Limited size, uncompressed TIFF only)
3. **COVERAGE Dataset** (Rejected: Copy-move only, 100 image pairs, insufficient for deep learning)
4. **CoMoFoD Dataset** (Rejected: Copy-move only, small sample size)

## Decision Outcome
**Chosen Option:** **Option 1: CASIA v2.0 (Primary) and CASIA v1.0 (Secondary)**

### Positive Consequences:
- **Broad Scale:** CASIA v2.0 provides 12,614 images across realistic indoor and outdoor natural scenes with varying dimensions.
- **Dual Forgery Scope:** Encompasses both copy-move (`Tp_S`) and splicing (`Tp_D`).
- **Community Ground Truth:** The `namtpham` GitHub repositories provide standardized binary localization masks and filename correction logs.
- **Cross-Dataset Validation:** CASIA v1.0 (1,721 images) serves as a secondary benchmark to test domain generalization.

### Negative Consequences:
- Original hosting server (`forensics.idealtest.org`) is frequently offline, requiring acquisition from community mirrors (Kaggle/HuggingFace).
- CASIA v2.0 contains known historical naming inconsistencies that require systematic preprocessing scripts.

## Status
**ACCEPTED** (2026-11-08)
