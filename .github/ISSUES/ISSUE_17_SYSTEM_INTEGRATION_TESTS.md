# [ISSUE #17] End-to-End System Integration & User Acceptance Test Suite

## 📌 Issue Metadata
- **Milestone:** M5 — Final Submission & Quality Assurance
- **Phase:** Phase 8 (Integration & Quality Assurance)
- **Estimated Effort:** 4–5 hours
- **Labels:** `testing`, `integration`, `uat`, `performance`, `qa`
- **Dependencies:** All previous issues (Issue #1 through Issue #16)
- **Blocks:** Academic Semester Project Submission

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Quality Assurance Lead & Systems Test Engineer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/testing/TESTING_STRATEGY.md`
> 2. `docs/testing/INTEGRATION_TESTING.md`
> 3. `docs/testing/ACCEPTANCE_TESTING.md`
> 4. `AGENTS.md` (Strict rules: Code coverage >80% on `src/`, all tests pass without CASIA datasets present, synthetic fixtures only).

---

## 🎯 Objective & Context
Implement end-to-end integration tests, latency profiling tests, and shared synthetic test fixtures across `tests/conftest.py` and `tests/test_performance.py`. Verify that the complete pipeline (upload $\rightarrow$ validation $\rightarrow$ preprocessing $\rightarrow$ neural inference $\rightarrow$ ELA rendering $\rightarrow$ dashboard view $\rightarrow$ PDF streaming $\rightarrow$ session cleanup) runs seamlessly within the $< 5.0\text{ s}$ latency boundary and achieves over 80% line test coverage across all `src/` modules.

---

## 📋 Technical Requirements

### 1. Pytest Configuration & Synthetic Fixtures (`tests/conftest.py`)
- Define shared fixtures using pure Python and Pillow (in-memory, no disk datasets required):
  - `app`: Instantiates Flask test application using test configuration.
  - `client`: Provides `app.test_client()`.
  - `synthetic_jpeg_bytes`: Generates valid JPEG binary buffer (`100x100`, RGB).
  - `synthetic_png_bytes`: Generates valid PNG binary buffer (`100x100`, RGB).
  - `synthetic_corrupt_bytes`: Byte string with invalid header bytes.
  - `synthetic_oversized_bytes`: Mock stream exceeding 16 MB.
  - `mock_predictor`: Monkeypatches `Predictor.predict()` to return deterministic test outputs when trained `.keras` files are not on disk.

### 2. End-to-End Pipeline Integration Tests (`tests/test_api.py` - Full Pipeline)
- **Test 1: Full Happy Path (JPEG):**
  - POST synthetic JPEG to `/analyze`.
  - Assert response is HTTP 200 or HTTP 302 redirect to result view.
  - Verify result view contains verdict, confidence, and ELA image path.
  - GET `/report/<session_id>`; verify HTTP 200, `application/pdf` mimetype, and non-empty byte stream.
- **Test 2: Full Happy Path (PNG):**
  - POST synthetic PNG to `/analyze`.
  - Verify pipeline handles PNG without raising an exception and renders ELA view.
- **Test 3: Malicious Payload Injection:**
  - POST executable payload disguised as `test.jpg`.
  - Assert server rejects payload with HTTP 400 Bad Request.
- **Test 4: Oversized File Protection:**
  - POST payload exceeding 16 MB.
  - Assert server returns HTTP 413 Payload Too Large.

### 3. Performance & Latency Profile Test (`tests/test_performance.py`)
- Benchmark wall-clock execution time for end-to-end `/analyze` calls across 10 repeated passes using CPU inference.
- Assert average processing duration is strictly under **5.0 seconds** per request (`NFR-001`).

---

## 📂 Target Files
- `tests/conftest.py`
- `tests/test_api.py` (completed)
- `tests/test_performance.py`

---

## 🧪 Verification & Testing
```bash
# Run complete test suite with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] All 17 test modules execute cleanly with zero test failures or errors.
- [ ] Code coverage across all modules in `src/` exceeds **80%**.
- [ ] End-to-end request turnaround meets the $< 5.0\text{ s}$ non-functional requirement.
- [ ] Entire test suite runs successfully in a clean environment without downloading the CASIA dataset.
