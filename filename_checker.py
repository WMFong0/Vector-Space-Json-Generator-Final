
"""Filename sanitization utilities.

This module provides helper functions to sanitize arbitrary user-provided
names and filenames into filesystem-safe variants.
"""
from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)

_ALLOWED = re.compile(r"[A-Za-z0-9_-]")
_SEP = "_"


def sanitize_basename(name: str) -> str:
    """Return a filesystem-safe base name.

    All characters not matching ``[A-Za-z0-9_-]`` are replaced with ``_``.
    Collapses consecutive underscores and strips them from both ends.
    Falls back to ``'file'`` if the sanitized value becomes empty.

    Parameters
    ----------
    name: str
        The input base name (no extension).

    Returns
    -------
    str
        A safe base name suitable for file paths.
    """
    if name is None:
        logger.debug("sanitize_basename: received None, using 'file' fallback")
        return "file"
    out = [ch if _ALLOWED.match(ch) else _SEP for ch in str(name)]
    collapsed = re.sub(r"_+", "_", "".join(out)).strip("_")
    safe = collapsed or "file"
    logger.debug("sanitize_basename: input=%r collapsed=%r safe=%r", name, collapsed, safe)
    return safe


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename while preserving the extension, if any.

    Parameters
    ----------
    filename: str
        Arbitrary filename possibly containing a path.

    Returns
    -------
    str
        A sanitized filename ``<safe_base><ext>``.
    """
    base, ext = os.path.splitext(os.path.basename(filename or ""))
    safe = f"{sanitize_basename(base)}{ext}"
    logger.debug("sanitize_filename: filename=%r -> %r", filename, safe)
    return safe


def filter_name(original_name: str) -> str | None:
    """Sanitize a line value into a safe base name or return ``None`` for empty.

    Parameters
    ----------
    original_name: str
        A line/text entry which may be empty.

    Returns
    -------
    Optional[str]
        Sanitized base name if non-empty, otherwise ``None``.
    """
    if not original_name:
        logger.debug("filter_name: empty input -> None")
        return None
    safe = sanitize_basename(original_name)
    logger.debug("filter_name: input=%r -> %r", original_name, safe)
    return safe


UPLOAD_ID_RE = re.compile(r"^[a-f0-9]{32}$", re.IGNORECASE)
