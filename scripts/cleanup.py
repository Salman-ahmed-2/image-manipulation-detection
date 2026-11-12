"""Purge expired session-scoped uploads and generated forensic artifacts."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class CleanupSummary:
    """Summarize one temporary-upload cleanup sweep."""

    directories_inspected: int
    directories_eligible: int
    directories_purged: int
    reclaimed_bytes: int


def _directory_size_bytes(directory: Path) -> int | None:
    """Measure regular file payload sizes beneath a session directory.

    Args:
        directory: Session directory to measure.

    Returns:
        Total file size in bytes, or None when an entry could not be inspected.
    """
    total_bytes = 0
    failed = False

    def report_walk_error(error: OSError) -> None:
        """Record a filesystem walk error and mark the size as incomplete.

        Args:
            error: Error raised while traversing the session directory.
        """
        nonlocal failed
        failed = True
        logger.warning("Unable to inspect temporary files during cleanup: %s", error)

    for root, _, filenames in os.walk(directory, onerror=report_walk_error):
        for filename in filenames:
            file_path = Path(root) / filename
            try:
                file_stat = file_path.stat(follow_symlinks=False)
                if stat.S_ISREG(file_stat.st_mode):
                    total_bytes += file_stat.st_size
            except OSError as error:
                failed = True
                logger.warning("Unable to measure a temporary file during cleanup: %s", error)

    return None if failed else total_bytes


def cleanup_uploads(
    max_age_minutes: int,
    dry_run: bool = False,
    force: bool = False,
) -> CleanupSummary:
    """Remove expired session directories from the configured upload folder.

    Args:
        max_age_minutes: Age threshold for deletion, in minutes.
        dry_run: If True, log eligible directories without deleting them.
        force: If True, consider every session directory eligible regardless of age.

    Returns:
        Counts of inspected, eligible, and purged directories and reclaimed bytes.

    Raises:
        ValueError: If max_age_minutes is negative.
    """
    if max_age_minutes < 0:
        raise ValueError("max_age_minutes must be zero or greater.")

    upload_folder = Path(Config.UPLOAD_FOLDER)
    max_age_seconds = timedelta(minutes=max_age_minutes).total_seconds()
    inspected = 0
    eligible = 0
    purged = 0
    reclaimed_bytes = 0

    try:
        with os.scandir(upload_folder) as scan:
            entries = list(scan)
    except OSError as error:
        logger.warning("Unable to scan the configured upload folder: %s", error)
        return CleanupSummary(inspected, eligible, purged, reclaimed_bytes)

    current_time = time.time()
    for entry in entries:
        try:
            if not entry.is_dir(follow_symlinks=False):
                continue
        except OSError as error:
            logger.warning("Unable to inspect an upload entry during cleanup: %s", error)
            continue

        inspected += 1
        directory = Path(entry.path)
        try:
            age_seconds = current_time - os.path.getmtime(directory)
        except OSError as error:
            logger.warning("Unable to determine a session directory's age: %s", error)
            continue

        if not force and age_seconds <= max_age_seconds:
            continue

        eligible += 1
        if dry_run:
            logger.info("Dry run: session directory %s is eligible for cleanup.", directory.name)
            continue

        size_before_removal = _directory_size_bytes(directory)
        if size_before_removal is None:
            continue

        try:
            shutil.rmtree(directory)
        except OSError as error:
            logger.warning("Unable to purge a session directory: %s", error)
            remaining_bytes = _directory_size_bytes(directory)
            if remaining_bytes is not None:
                reclaimed_bytes += max(0, size_before_removal - remaining_bytes)
        else:
            purged += 1
            reclaimed_bytes += size_before_removal
            logger.info("Purged an expired temporary session directory.")

    return CleanupSummary(inspected, eligible, purged, reclaimed_bytes)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for temporary upload cleanup.

    Returns:
        An argument parser for cleanup options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-age-minutes",
        type=int,
        default=Config.TEMP_FILE_EXPIRY // 60,
        help="Age threshold for session directories in minutes.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report eligible directories without deleting them.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Purge every session directory regardless of age.",
    )
    return parser


def main() -> None:
    """Parse cleanup options, run the sweep, and log its summary."""
    parser = _build_argument_parser()
    arguments = parser.parse_args()
    if arguments.max_age_minutes < 0:
        parser.error("--max-age-minutes must be zero or greater.")

    summary = cleanup_uploads(
        max_age_minutes=arguments.max_age_minutes,
        dry_run=arguments.dry_run,
        force=arguments.force,
    )
    reclaimed_megabytes = summary.reclaimed_bytes / (1024 * 1024)
    logger.info(
        "Cleanup summary: inspected=%d eligible=%d purged=%d reclaimed=%.2f MB",
        summary.directories_inspected,
        summary.directories_eligible,
        summary.directories_purged,
        reclaimed_megabytes,
    )


if __name__ == "__main__":
    main()
