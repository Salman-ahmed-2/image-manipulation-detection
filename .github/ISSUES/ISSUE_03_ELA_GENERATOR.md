# [ISSUE #3] Error Level Analysis (ELA) Forensic Generator Module

## 📌 Issue Metadata
- **Milestone:** M1 — Data Pipeline & Forensics
- **Phase:** Phase 2 (Forensics & Preprocessing)
- **Estimated Effort:** 3–4 hours
- **Labels:** `forensics`, `ela`, `image-processing`, `pillow`
- **Dependencies:** Issue #1 (`config.py`), Issue #2 (`src/utils/`)
- **Blocks:** Issue #11 (`ela_service.py`), Issue #16 (`result.html`)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Digital Image Forensics Engineer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/image_forensics/ELA_OVERVIEW.md`
> 2. `docs/image_forensics/ELA_IMPLEMENTATION.md`
> 3. `docs/image_forensics/ELA_LIMITATIONS.md`
> 4. `AGENTS.md` (Strict rules: ELA lives ONLY in `src/preprocessing/ela_generator.py`, Pillow only, PNG warning required, never claim ELA proves tampering).

---

## 🎯 Objective & Context
Implement the core Error Level Analysis (ELA) generation engine in `src/preprocessing/ela_generator.py`. The module accepts an image, recompresses it in-memory to JPEG at a controlled quality factor (default 90), computes the absolute pixel-wise difference against the original, enhances the residual (10x multiplier), and returns the amplified ELA visualization map as a PIL Image or PNG file. Write comprehensive unit tests in `tests/test_ela.py`.

---

## 📋 Technical Requirements

### 1. `ELAGenerator` Class (`src/preprocessing/ela_generator.py`)
- Implement `class ELAGenerator`:
  ```python
  class ELAGenerator:
      @staticmethod
      def generate(
          image_input: Union[str, Path, Image.Image],
          output_path: Optional[Union[str, Path]] = None,
          quality: int = 90,
          enhancement_factor: float = 10.0
      ) -> Image.Image:
          """Generate an Error Level Analysis visualization for an image.
          
          Args:
              image_input: Absolute file path or pre-loaded PIL Image object.
              output_path: Optional destination path to save the generated PNG.
              quality: JPEG recompression quality factor (1-95). Defaults to 90.
              enhancement_factor: Brightness multiplier applied to pixel differences.
              
          Returns:
              A PIL Image object containing the enhanced ELA visualization.
              
          Raises:
              FileNotFoundError: If image file path does not exist.
              ValueError: If quality is outside 1-95 or factor <= 0.
              IOError: If image cannot be decoded.
          """
  ```
- **Image Conversion:** Ensure input is converted to 3-channel RGB.
- **PNG Warning:** If input path ends with `.png`, log a warning:  
  `logger.warning("Source image is PNG. ELA on PNG introduces an artificial baseline error across the canvas.")`
- **In-Memory Recompression:** Save to `io.BytesIO` as JPEG at `quality=quality` (do not write unnecessary temporary files to disk during the diff calculation).
- **Difference Computation:** Reload from BytesIO and execute `ImageChops.difference(original_rgb, recompressed_rgb)`.
- **Contrast Amplification:** Use `ImageEnhance.Brightness(diff_img).enhance(enhancement_factor)`.
- **Output Handling:** If `output_path` is provided, save as PNG to preserve exact difference artifacts. Return the PIL Image object.

### 2. Unit Test Suite (`tests/test_ela.py`)
- Test with synthetic RGB JPEG images created with `PIL.Image.new()`.
- Test that output ELA image matches original image width and height.
- Test that output mode is `"RGB"`.
- Test PNG input executes and logs expected warning without raising an exception.
- Test invalid quality values (`quality=0` or `quality=100`) raise `ValueError`.
- Test negative or zero `enhancement_factor` raises `ValueError`.

---

## 📂 Target Files
- `src/preprocessing/ela_generator.py`
- `tests/test_ela.py`

---

## 🧪 Verification & Testing
```bash
pytest tests/test_ela.py -v
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] `ELAGenerator.generate()` runs in memory using `io.BytesIO` without disk clutter.
- [ ] Output ELA image has identical dimensions to the source image.
- [ ] PNG inputs trigger the forensic diagnostic log warning.
- [ ] Boundary conditions (invalid quality factors or negative enhancement) raise `ValueError`.
- [ ] `pytest tests/test_ela.py` passes 100%.
