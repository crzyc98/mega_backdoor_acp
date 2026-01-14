"""Storage utilities for atomic file operations."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Union


def atomic_write(file_path: Union[str, Path], content: str) -> None:
    """
    Write content to a file atomically using temp file + rename pattern.

    This ensures that readers never see a partially written file.

    Args:
        file_path: Path to the target file
        content: Content to write
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in the same directory (ensures same filesystem for rename)
    fd, temp_path = tempfile.mkstemp(
        dir=file_path.parent,
        prefix=f".{file_path.name}.",
        suffix=".tmp"
    )

    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)

        # Atomic rename
        os.replace(temp_path, file_path)
    except Exception:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
