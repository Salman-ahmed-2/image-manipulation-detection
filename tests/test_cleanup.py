"""Tests for the temporary session-directory cleanup script."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config import Config
from scripts import cleanup
from scripts.cleanup import cleanup_uploads


def test_cleanup_uploads_dry_run_reports_expired_directories_without_deleting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dry-run identifies old directories but leaves their contents untouched."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    expired_directory = tmp_path / "expired"
    expired_directory.mkdir()
    image_path = expired_directory / "image.jpg"
    image_path.write_bytes(b"synthetic image data")
    old_mtime = 1_000_000_000
    os.utime(expired_directory, (old_mtime, old_mtime))
    monkeypatch.setattr("scripts.cleanup.time.time", lambda: old_mtime + 3601)

    summary = cleanup_uploads(max_age_minutes=60, dry_run=True)

    assert summary.directories_inspected == 1
    assert summary.directories_eligible == 1
    assert summary.directories_purged == 0
    assert summary.reclaimed_bytes == 0
    assert image_path.exists()


def test_cleanup_uploads_purges_expired_directories_and_counts_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expired session files are removed and their payload bytes are reported."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    expired_directory = tmp_path / "expired"
    fresh_directory = tmp_path / "fresh"
    expired_directory.mkdir()
    fresh_directory.mkdir()
    image_path = expired_directory / "image.jpg"
    image_path.write_bytes(b"synthetic image data")
    old_mtime = 1_000_000_000
    os.utime(expired_directory, (old_mtime, old_mtime))
    monkeypatch.setattr("scripts.cleanup.time.time", lambda: old_mtime + 3601)

    summary = cleanup_uploads(max_age_minutes=60)

    assert summary.directories_inspected == 2
    assert summary.directories_eligible == 1
    assert summary.directories_purged == 1
    assert summary.reclaimed_bytes == len(b"synthetic image data")
    assert not expired_directory.exists()
    assert fresh_directory.exists()


def test_cleanup_uploads_force_purges_recent_session_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Force mode removes recent session folders regardless of their age."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    recent_directory = tmp_path / "recent"
    recent_directory.mkdir()
    file_path = recent_directory / "image.jpg"
    file_path.write_bytes(b"temporary")
    monkeypatch.setattr("scripts.cleanup.time.time", lambda: file_path.stat().st_mtime)

    summary = cleanup_uploads(max_age_minutes=30, force=True)

    assert summary.directories_purged == 1
    assert summary.reclaimed_bytes == len(b"temporary")
    assert not recent_directory.exists()


def test_cleanup_uploads_continues_after_a_removal_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed directory removal does not prevent later sessions from being purged."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    failed_directory = tmp_path / "cannot-remove"
    removable_directory = tmp_path / "remove"
    failed_directory.mkdir()
    removable_directory.mkdir()
    (failed_directory / "image.jpg").write_bytes(b"keep")
    (removable_directory / "image.jpg").write_bytes(b"remove")
    real_rmtree = cleanup.shutil.rmtree

    def remove_or_fail(path: str | os.PathLike[str]) -> None:
        """Raise an expected filesystem error for one directory.

        Args:
            path: Directory selected by the cleanup sweep.
        """
        if Path(path) == failed_directory:
            raise PermissionError("synthetic permission failure")
        real_rmtree(path)

    monkeypatch.setattr(cleanup.shutil, "rmtree", remove_or_fail)
    monkeypatch.setattr(cleanup.time, "time", lambda: 10_000_000_000)

    summary = cleanup_uploads(max_age_minutes=0)

    assert summary.directories_purged == 1
    assert summary.reclaimed_bytes == len(b"remove")
    assert failed_directory.is_dir()
    assert not removable_directory.exists()
