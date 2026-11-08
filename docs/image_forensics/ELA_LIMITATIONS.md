# Limitations, Failure Modes, and Anti-Patterns of ELA

## 1. Fundamental Physical Limitations
While Error Level Analysis provides intuitive visual feedback, it is fundamentally an **indirect heuristic** rather than a mathematical proof of forgery. It relies upon fragile assumptions regarding compression history that frequently fail in real-world environments.

---

## 2. Common False Positives (Authentic Regions Flagged as Bright)

```
High Natural Contrast / Sharp Texture -> Higher DCT Residual -> Bright ELA Appearance -> False Alarm
```

1. **High-Frequency Natural Textures:** Intricate foliage, fine fabric weaves, gravel, and animal fur naturally generate large high-frequency DCT coefficients that produce high recompression errors, resulting in bright ELA patches on pristine imagery.
2. **Sharp Contrast Edges:** The boundary between dark hair and a pale background, building silhouettes against a bright sky, or sharp typographic text naturally produces high quantization residuals along $8 \times 8$ boundary lines.
3. **PNG and Lossless Format Conversions:** PNG images lack native quantization tables. Converting a PNG into JPEG for ELA testing creates a uniform high-intensity error floor that can easily be misinterpreted by untrained users.

---

## 3. Common False Negatives (Manipulations Completely Missed)

1. **Low-Quality Multi-Generation JPEGs:** When an image has been uploaded, shared, and re-saved multiple times (e.g. across WhatsApp, Facebook, or Twitter), its compression error profile has completely converged to uniform equilibrium. Splicing traces are smoothed away by repeated lossy passes.
2. **Matching Quantization Tables:** If a skilled manipulator extracts an object from an authentic image that was compressed using the exact same camera quantization matrix as the target image, ELA cannot differentiate between them.
3. **Post-Tampering Blurring or Retouching:** Deliberate Gaussian blur or median filtering applied across splicing seams degrades the high-frequency DCT mismatch that ELA relies on.

---

## 4. Complementary Synthesis: ELA + Deep Learning
To counteract ELA's limitations, the **Image Manipulation Detection System** synthesizes physical heuristics with deep feature extraction:
- **ELA:** Provides human-interpretable visual localization and transparent screening cues.
- **Deep Convolutional Models (CNN & MobileNetV2):** Learn non-linear, multi-scale spatial noise correlations, camera sensor pattern noise (PRNU), and subtle interpolation traces that bypass human visual perception.
