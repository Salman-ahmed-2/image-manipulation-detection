# PDF Report Generation Specification (`src/services/report_service.py`)

## 1. Document Overview
The report generation service assembles analysis results, original image thumbnails, high-contrast ELA maps, prediction metrics, and legal disclaimers into a standardized, single-page or two-page PDF document.

---

## 2. Report Document Layout

```
+-------------------------------------------------------------------+
|  [LOGO] IMAGE MANIPULATION DETECTION SYSTEM                       |
|         Automated Preliminary Forensic Screening Report           |
+-------------------------------------------------------------------+
| Report ID: 7c9e6679-...           Generated: 2026-11-08 14:30 UTC |
| Model Used: MobileNetV2           Active Quality Factor: 90       |
+-------------------------------------------------------------------+
| PREDICTION VERDICT:                                               |
| [=================== 94.2% CONFIDENCE ==========================] |
| Verdict: POTENTIALLY MANIPULATED                                  |
+-------------------------------------------------------------------+
| VISUAL FORENSIC COMPARISON:                                       |
|                                                                   |
| +-------------------------+     +-------------------------------+ |
| |                         |     |                               | |
| |    ORIGINAL IMAGE       |     |     ERROR LEVEL ANALYSIS      | |
| |       (Ingested)        |     |          (10x Scale)          | |
| |                         |     |                               | |
| +-------------------------+     +-------------------------------+ |
|                                                                   |
+-------------------------------------------------------------------+
| METADATA & TECHNICAL SUMMARY:                                     |
| Dimensions: 1024 x 768 px       Input Colorspace: RGB             |
| File Size: 1.84 MB              Inference Latency: 78 ms          |
+-------------------------------------------------------------------+
| ⚠️ MANDATORY FORENSIC DISCLAIMER:                                  |
| This report provides preliminary screening only and does not      |
| constitute definitive judicial evidence. ELA is an investigative  |
| aid; bright regions represent compression variance, not guilt.    |
+-------------------------------------------------------------------+
```

---

## 3. Technology Selection: `fpdf2`
- **Library:** `fpdf2` (Python 3 port of FPDF).
- **Rationale:** Pure Python, zero native system dependencies (unlike `weasyprint` which requires Cairo and Pango), lightweight, fast compilation ($< 250\text{ ms}$ per report).
