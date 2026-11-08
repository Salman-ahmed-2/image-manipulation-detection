# Non-Functional Requirements Specification

## 1. Performance and Latency Requirements

### NFR-001: End-to-End Processing Latency
- **Category:** Performance.
- **Specification:** The total time elapsed from form submission (`POST /analyze`) to complete HTML rendering of the results dashboard must not exceed **5.0 seconds** for an average 3.0 MB image running on a standard 4-core CPU host (without GPU acceleration).
- **Sub-Component Budgets:**
  - File Validation & I/O: $\le 0.4 \text{ s}$
  - Image Preprocessing: $\le 0.6 \text{ s}$
  - Neural Inference (MobileNetV2 or CNN): $\le 1.8 \text{ s}$
  - ELA Recompression & Scaling: $\le 1.5 \text{ s}$
  - Template Composition & Network Transfer: $\le 0.7 \text{ s}$
- **Measurement Criteria:** Automated benchmark runs across 50 test images measuring wall-clock duration via `tests/test_performance.py`.
- **Priority:** High.

### NFR-002: Model Cold-Start vs. In-Memory Resident State
- **Category:** Performance / Efficiency.
- **Specification:** Models must be loaded into memory **once** during Flask application startup (`model_loader.py`). Under zero circumstances should model weights be re-instantiated or re-read from disk during an HTTP request.
- **Target Overhead:** Cold start $\le 8.0 \text{ s}$ during application initialization; zero request-time loading overhead.
- **Priority:** Critical.

---

## 2. Resource Constraints and Capacity

### NFR-003: Payload and Memory Boundaries
- **Category:** Scalability / Reliability.
- **Specification:** 
  - Maximum upload request payload is strictly capped at **16 MB** (`Config.MAX_CONTENT_LENGTH = 16 * 1024 * 1024`).
  - Single-worker memory consumption during active inference and ELA rendering must remain below **500 MB RAM**.
- **Measurement Criteria:** Monitored via Linux `psrecord` / memory profiling during simultaneous execution of 5 concurrent requests.
- **Priority:** High.

### NFR-004: Ephemeral Disk Budget
- **Category:** Storage Management.
- **Specification:** Temporary storage under `temp/uploads/` must never exceed **2.0 GB** in aggregate. Stale session directories older than 30 minutes must be automatically reaped by a background daemon or request-hook sweep.
- **Priority:** High.

---

## 3. Security and Data Privacy

### NFR-005: Zero Persistent Data Policy
- **Category:** Security / Privacy.
- **Specification:** The system must not store user images, derived ELA representations, or analysis telemetry permanently. No relational database, document database, or object storage bucket shall retain user media after session conclusion.
- **Priority:** Critical.

### NFR-006: Payload Hardening and Magic Byte Verification
- **Category:** Security.
- **Specification:** File validation must not rely solely on client-supplied MIME headers or file extensions. The system must inspect binary magic byte headers (`FF D8 FF` for JPEG, `89 50 4E 47` for PNG) before handing the byte stream to PIL or OpenCV decoding routines.
- **Priority:** Critical.

### NFR-007: Filename Sanitization and Path Traversal Prevention
- **Category:** Security.
- **Specification:** User-supplied filenames must be stripped of relative directory traversals (`../`, `..\`) via `werkzeug.utils.secure_filename` and assigned a cryptographically random UUID4 prefix prior to writing to the filesystem.
- **Priority:** Critical.

---

## 4. Usability and Accessibility

### NFR-008: Responsive Layout and Cross-Browser Parity
- **Category:** Usability.
- **Specification:** The web application interface must render cleanly without horizontal scrollbars across screen viewports ranging from 375px (mobile portrait) to 2560px (ultra-wide desktop).
- **Supported Browsers:** Google Chrome (latest 3 versions), Mozilla Firefox (latest 3 versions), Safari (latest 2 versions), Microsoft Edge (latest 2 versions).
- **Priority:** Medium.

### NFR-009: Transparency and Mandatory Disclaimers
- **Category:** Legal / Academic Integrity.
- **Specification:** Every view displaying an ELA visualization or model prediction must feature the authoritative disclaimer:
  > *"ELA visualization is an investigative aid. Bright regions indicate potential compression inconsistencies and do not constitute definitive proof of digital manipulation."*
- **Priority:** Critical.

---

## 5. Maintainability and Software Quality

### NFR-010: Code Standards and Architectural Boundaries
- **Category:** Maintainability.
- **Specification:**
  - 100% of Python code must adhere to PEP 8 standards with a line-length limit of 100 characters.
  - Every public function and class must include Google-style docstrings with explicit `Args`, `Returns`, and `Raises` definitions.
  - Type annotations must be present across all function signatures.
  - Test suite coverage across all modules in `src/` must exceed **80%** as verified by `pytest --cov=src`.
- **Priority:** High.
