import os
from pathlib import Path
from typing import List, Optional

from sigmate.utils.ignore import CustomIgnoreMatcher
from sigmate.config import DEFAULT_EXCLUDED_EXTENSIONS
from sigmate.utils.logger import Logger


def should_skip_file(path: Path) -> bool:
    """Determines if a file should be skipped based on its name or extension."""
    name = path.name.lower()
    return (
        name.endswith(".lock")
        or name.startswith(".")
        or path.suffix in DEFAULT_EXCLUDED_EXTENSIONS
    )


def collect_files(base_dir: Path, logger: Optional[Logger] = None) -> List[Path]:
    """
    Collects all files in a directory recursively, respecting ignore rules
    from .sigmateignore or .gitignore using the CustomIgnoreMatcher.
    """
    matcher = CustomIgnoreMatcher(base_dir, logger=logger)
    collected: List[Path] = []

    for root_str, dirnames, filenames in os.walk(base_dir, topdown=True):
        root_path = Path(root_str)

        # Filter out directories to prevent traversal.
        # This filters hidden directories and those matching ignore patterns.
        dirnames[:] = [
            d
            for d in dirnames
            if not d.startswith(".") and not matcher.matches(root_path / d, is_dir=True)
        ]

        for filename in filenames:
            file_path = root_path / filename
            # Skip symlinks for safety and check against ignore rules.
            if not file_path.is_symlink():
                if not should_skip_file(file_path) and not matcher.matches(
                    file_path, is_dir=False
                ):
                    collected.append(file_path.resolve())
            elif logger:
                logger.debug(f"Skipping symlink: {file_path}", emoji="🔗")

    if logger:
        logger.debug(
            f"Collected {len(collected)} files from {base_dir} (after applying ignore rules)",
            emoji="📁",
        )
    return collected


def build_output_path(
    file_path: Path,
    content_processing_base_dir: Path,
    extension_suffix: str,
    overall_output_root_dir: Path,
) -> Path:
    """
    Constructs a parallel output path for a generated artifact (e.g., .sig file).
    The structure under overall_output_root_dir will mirror the structure of
    file_path relative to content_processing_base_dir.
    """
    try:
        relative_content_path = file_path.resolve().relative_to(
            content_processing_base_dir.resolve()
        )
    except ValueError:
        # Fallback if file_path is not under content_processing_base_dir
        relative_content_path = Path(file_path.name)

    artifact_output_path = (
        overall_output_root_dir.resolve()
        / relative_content_path.with_suffix(file_path.suffix + extension_suffix)
    )

    artifact_output_path.parent.mkdir(parents=True, exist_ok=True)
    return artifact_output_path


def is_binary(path: Path, blocksize: int = 512, sample_blocks: int = 3) -> bool:
    """Heuristically determines if a file is binary by checking for null bytes."""
    try:
        with path.open("rb") as f:
            for _ in range(sample_blocks):
                chunk = f.read(blocksize)
                if not chunk:
                    break
                if b"\0" in chunk:
                    return True
        return False
    except Exception:
        return True
