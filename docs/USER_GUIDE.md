# User Guide: Image Manipulation Detection System

## 1. Introduction
Welcome to the **Image Manipulation Detection System**. This application provides a web-based, preliminary investigative screening tool designed to help journalists, students, researchers, and general users evaluate whether a digital photograph shows signs of manipulation or tampering (such as copy-move cloning or image splicing).

---

## 2. Navigating the Interface

### 2.1 The Navigation Bar
Located at the top of every screen:
- **Brand / Home (`/`):** Returns to the image submission portal.
- **About (`/about`):** Detailed background on digital image forensics, ELA theory, deep learning models, and student team credits.
- **Documentation Link:** Quick reference to user guides and forensic interpretation standards.

---

## 3. Step-by-Step Analysis Workflow

### Step 1: Uploading an Image
1. Open your browser and navigate to the application address (typically `http://localhost:5000` or the hosted demonstration URL).
2. On the home page, locate the **Upload Box**.
3. You can either:
   - **Drag and drop** an image file directly into the designated drop-zone.
   - Click **"Browse Files"** and select a file from your computer.
4. **Supported File Types:** JPEG (`.jpg`, `.jpeg`) and PNG (`.png`).
5. **Maximum File Size:** 16 Megabytes (MB).
6. Once selected, an instant thumbnail preview of your selected image will appear in the viewport.

### Step 2: Selecting Model (Optional)
- By default, the system runs with the recommended **MobileNetV2** transfer learning model for rapid, robust inference.
- Advanced users may select the **Custom CNN** model from the model dropdown selector to contrast architectures.

### Step 3: Initiating Analysis
- Click the prominent blue **"Analyze Image"** button.
- A progress spinner will appear indicating the image is undergoing server-side validation, deep-learning tensor analysis, and Error Level Analysis (ELA) generation.
- Analysis typically completes within **2 to 5 seconds**.

### Step 4: Reviewing Results Dashboard
Upon completion, the application automatically redirects to the **Analysis Dashboard**:
- **Authenticity Verdict:** Prominently displayed at the top:
  - 🟢 **Authentic Image:** The deep learning model found minimal statistical evidence of tampering.
  - 🔴 **Potentially Manipulated:** The deep learning model detected anomalous structural patterns characteristic of digital manipulation.
- **Confidence Metric:** A percentage bar indicating model certainty (e.g., 94.2% confidence).
- **Side-by-Side Visual Comparison:**
  - **Left Card:** Original Uploaded Image.
  - **Right Card:** Error Level Analysis (ELA) visualization map.
- **Interactive Controls:** Toggle between side-by-side comparison and split-screen overlay.

### Step 5: Exporting Forensic Report
- To archive your findings, click the green **"Download PDF Report"** button located at the bottom of the dashboard.
- A clean, multi-page PDF will be generated immediately containing the original thumbnail, ELA output, confidence statistics, timestamp, and legal disclaimers.

---

## 4. How to Interpret Error Level Analysis (ELA)
Error Level Analysis operates by recompressing the photograph at a known quality level (90%) and amplifying the difference between the original pixels and the recompressed version.

| Visual Pattern | Typical Meaning | Note / Caution |
| :--- | :--- | :--- |
| **Uniform, Dim Gray Texture** | Consistent compression history across the entire image surface | Typical of an untouched authentic photograph. |
| **Noticeably Brighter Localized Region** | Region has a different compression history than surrounding areas | May indicate a foreign element spliced from another source. |
| **Bright High-Frequency Edges / Text** | Normal compression behavior around sharp high-contrast transitions | **Not necessarily manipulation.** Sharp natural edges naturally compress with higher residual error. |
| **Completely Black / Dark Canvas** | Image has been resaved many times at low quality and reached equilibrium | ELA cannot effectively detect edits once an image is heavily recompressed. |

> ⚠️ **IMPORTANT FORENSIC DISCLAIMER:**
> ELA visualization is an investigative screening aid. Bright areas in an ELA image indicate potential compression discrepancies and do NOT constitute definitive proof of digital manipulation. Always combine ELA inspection with model confidence metrics and contextual research.

---

## 5. Frequently Asked Questions (FAQ)

**Q: Does the application store my uploaded photos?**  
A: **No.** The system adheres to strict data privacy principles. Uploaded images are stored in temporary, randomized session folders and automatically deleted after report generation or session expiration.

**Q: Can this software detect AI-generated imagery (e.g., Midjourney, DALL-E)?**  
A: The core models are trained on classical photographic tampering benchmarks (CASIA v1.0 and v2.0), specifically targeting copy-move cloning and splicing. While synthetic AI images may exhibit anomalous ELA patterns, the tool is not certified as a dedicated diffusion-model detector.

**Q: Why does my PNG image show high brightness across the entire ELA map?**  
A: PNG is a lossless format that lacks native JPEG quantization tables. When analyzing a PNG, the system must first convert the file to JPEG, introducing baseline compression artifacts across the entire surface.
