"""Safe, local-only candidate verification and atomic replacement.

Never mutate an original source file while static analysis is running.
This is not an autonomous repair loop or a multi-process locking system.
"""
from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Callable, Any


def resolve_source(root_dir: str | Path, relative: str) -> Path:
    root = Path(root_dir).resolve(strict=True)
    rel = Path(relative)
    if (not relative or rel.is_absolute() or ".." in rel.parts
            or ".git" in rel.parts):
        raise ValueError("Source path must be a regular file inside the repository")
    target = root
    for component in rel.parts:
        target = target / component
        # Checking only the final component lets aliases to .git/ bypass
        # the protected-path rule, even when the alias stays inside root.
        if target.is_symlink():
            raise ValueError("Symlinked source path components are not allowed")
    resolved = target.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("Source file escapes the selected repository")
    if ".git" in resolved.relative_to(root).parts or not target.is_file():
        raise ValueError("Only regular source files outside Git metadata can be edited")
    return target


def apply_verified_edit(
    root_dir: str | Path,
    relative: str,
    new_text: str,
    analyze: Callable[[str], list[dict[str, Any]]],
) -> bool:
    """Validate a sibling candidate before atomically replacing the original.

    Return False for reported static diagnostics. Raise on missing tools,
    invalid paths, analysis failures or concurrent changes. No filename from
    the caller is ever passed to a shell.
    """
    if not isinstance(new_text, str):
        raise ValueError("New content must be UTF-8 text")
    root = Path(root_dir).resolve(strict=True)
    target = resolve_source(root, relative)
    source_stat = target.stat(follow_symlinks=False)
    if not stat.S_ISREG(source_stat.st_mode):
        raise ValueError("Not a regular file")
    before = target.read_bytes()
    candidate: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            prefix=f".{target.stem}-candidate-",
            suffix=target.suffix,
            dir=target.parent,
            delete=False,
        ) as handle:
            candidate = Path(handle.name)
            handle.write(new_text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(candidate, stat.S_IMODE(source_stat.st_mode))

        diagnostics = analyze(candidate.relative_to(root).as_posix())
        if not isinstance(diagnostics, list):
            raise RuntimeError("Static analyzer returned no usable diagnostic result")
        if diagnostics:
            return False

        # Revalidate path components after invoking an external analyzer.
        # This is not a replacement for OS-level multi-process locking.
        resolve_source(root, relative)
        current_stat = target.stat(follow_symlinks=False)
        if (target.is_symlink()
                or current_stat.st_ino != source_stat.st_ino
                or current_stat.st_dev != source_stat.st_dev
                or target.read_bytes() != before):
            raise RuntimeError("Source changed during static analysis; edit aborted")
        os.replace(candidate, target)
        candidate = None
        return True
    finally:
        if candidate is not None:
            candidate.unlink(missing_ok=True)
