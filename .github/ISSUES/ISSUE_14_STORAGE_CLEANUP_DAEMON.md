# [ISSUE #14] Ephemeral Storage Cleanup Daemon & Automated Maintenance

## 📌 Issue Metadata
- **Milestone:** M4 — Full Web Application & Reports
- **Phase:** Phase 6 (Forensic Reporting & Maintenance)
- **Estimated Effort:** 2–3 hours
- **Labels:** `maintenance`, `security`, `privacy`, `cleanup`
- **Dependencies:** Issue #1 (`config.py`), Issue #2 (`logger.py`)
- **Blocks:** Issue #17 (System Testing)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a DevOps & Security Engineer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/SECURITY_GUIDELINES.md`
> 2. `docs/DATABASE_DESIGN.md`
> 3. `AGENTS.md` (Strict rules: Zero permanent image storage, purge session folders older than 30 minutes, defensive error handling).

---

## 🎯 Objective & Context
Implement `scripts/cleanup.py` and automatic cleanup hooks inside the application. To respect user confidentiality and adhere to forensic privacy standards, user-uploaded photographs and generated ELA maps must never be retained permanently on disk. The cleanup script scans `temp/uploads/`, identifies session directories older than `Config.TEMP_FILE_EXPIRY` (30 minutes), and removes them cleanly.

---

## 📋 Technical Requirements

### 1. Cleanup Utility (`scripts/cleanup.py`)
- Implement CLI script with options:
  - `--max-age-minutes` (int, default 30): Age threshold for purging directories.
  - `--dry-run` (bool, default False): Log which directories would be deleted without removing them.
  - `--force` (bool, default False): Purge all session folders immediately regardless of age.
- Functionality:
  - Scan `Config.UPLOAD_FOLDER` (or `temp/uploads/`).
  - Calculate directory age using modification timestamp: `time.time() - os.path.getmtime(dir_path)`.
  - Safely remove expired folders via `shutil.rmtree()`.
  - Log summary: Total directories inspected, total purged, disk space reclaimed (MB).
  - Catch `OSError` / `PermissionError` and log warnings without aborting the sweep.

### 2. Python Helper Function in `src/utils/file_validator.py`
- Implement `cleanup_session_directory(session_id: str) -> bool`:
  - Directly removes `Config.UPLOAD_FOLDER / session_id` if it exists.
  - Called immediately after a user downloads their PDF report or navigates home.

---

## 📂 Target Files
- `scripts/cleanup.py`
- `src/utils/file_validator.py` (enhanced)

---

## 🧪 Verification & Testing
```bash
# Test cleanup dry-run
python3 scripts/cleanup.py --dry-run
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] `scripts/cleanup.py` safely purges stale session folders older than 30 minutes.
- [ ] `--dry-run` and `--force` flags work as specified.
- [ ] Reclaimed disk space and file counts are logged accurately.
- [ ] Zero user images remain permanently on the server disk.
