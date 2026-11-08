# Comprehensive System Limitations & Disclaimers

## 1. System Scope Boundaries
The **Image Manipulation Detection System** is explicitly engineered as an educational, preliminary screening utility. It is **not** certified as a legal-evidentiary forensic tool and must not be used as sole evidence in judicial proceedings, disciplinary actions, or criminal investigations.

---

## 2. Inherent Algorithmic Limitations

### 2.1 Error Level Analysis (ELA) Limitations
- **JPEG Specificity:** ELA is fundamentally designed around the lossy Discrete Cosine Transform (DCT) quantization characteristics of the JPEG standard. It cannot detect manipulation on raw bitmaps, vector graphics, or non-lossy formats without introducing artificial baseline noise.
- **Edge False Positives:** Sharp high-frequency contrast transitions (e.g. black text on a white page, silhouette edges) naturally generate high recompression errors and appear intensely bright even on pristine photographs.
- **Multi-Generation Degradation:** Photographs that have passed through social media re-encoding pipelines (e.g. WhatsApp, Facebook, Instagram) have had their subtle compression residuals homogenized, rendering ELA largely blind to historical splices.

### 2.2 Deep Learning Model Limitations
- **Dataset Bias:** Models trained on the CASIA benchmark inherit the specific camera sensors, post-processing filters, and manipulation techniques present in the 2000s-era CASIA images. Real-world modern smartphone images or AI-generated imagery may trigger out-of-distribution prediction uncertainty.
- **Whole-Image Binary Classification:** The current core models produce a whole-image verdict (Authentic vs. Manipulated) rather than pixel-level localization masks.
- **Adversarial Susceptibility:** Like all convolutional neural networks, the models can be susceptible to targeted adversarial perturbations or deliberate anti-forensic post-processing (e.g. median filtering over splicing boundaries).

---

## 3. Mandatory Ethical Disclaimer

> **AUTHORITATIVE ETHICAL & FORENSIC NOTICE:**  
> This system is designed for preliminary image authenticity screening, not professional forensic certification. Predictions and ELA visualizations provide investigative cues and statistical probabilities, not definitive proof of authenticity or manipulation. Independent expert human review and multi-modal forensic verification remain mandatory for critical or legal determinations.
