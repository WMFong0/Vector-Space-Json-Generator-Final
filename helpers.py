"""Helper functions for the PDF processing app."""

from __future__ import annotations

import json
import logging
import os
import shutil
import time
import uuid
import zipfile
from typing import Iterable

import filename_checker
from config import ALLOWED_OSC, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_LOADER, DEFAULT_SPLITTER, IMAGE_BASED_CHUNK_SIZE, IMAGE_BASED_LOADER, LARGE_DOCUMENT_CHUNK_SIZE, MAX_AGE_SECONDS, RUNS_ROOT, UPLOAD_ROOT, UPLOAD_ID_RE, logger

def _allowed_file(filename: str) -> bool:
    """Return True if the file extension is .pdf (case-insensitive)."""
    return os.path.splitext(filename.lower())[1] == ".pdf"


def _sanitize_zip_name(filename: str) -> str:
    """Sanitize a filename for use inside the ZIP archive."""
    return filename_checker.sanitize_filename(filename)


def _dedupe_zip_name(name: str, seen: set) -> str:
    """De-duplicate a name within a set by appending -N before extension."""
    if name not in seen:
        seen.add(name)
        return name
    base, ext = os.path.splitext(name)
    i = 2
    while f"{base}-{i}{ext}" in seen:
        i += 1
    cand = f"{base}-{i}{ext}"
    seen.add(cand)
    return cand


def _filter_names_from_list(names: Iterable[str]) -> list[str]:
    """Sanitize a list of filenames, preserving extensions; skip empties."""
    out: list[str] = []
    for line in names:
        if not line:
            continue
        base, ext = os.path.splitext(line)
        safe_base = filename_checker.filter_name(base)
        if safe_base is not None:
            out.append(f"{safe_base}{ext}")
    logger.debug("_filter_names_from_list: %r -> %r", list(names), out)
    return out


def _cleanup_old_sessions() -> None:
    """Delete session dirs older than MAX_AGE_SECONDS from runs/ and tmp_uploads/."""
    now = time.time()
    cutoff = now - MAX_AGE_SECONDS
    
    for root_dir in [RUNS_ROOT, UPLOAD_ROOT]:
        if not os.path.isdir(root_dir):
            continue
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            if os.path.isdir(item_path):
                mtime = os.path.getmtime(item_path)
                if mtime < cutoff:
                    try:
                        shutil.rmtree(item_path)
                        logger.info("Deleted old session dir: %s", item_path)
                    except OSError as exc:
                        logger.warning("Failed to delete %s: %s", item_path, exc)


def _generate_loaders(
    name_list: list[str],
    folder_name: str,
    image_set: set[str],
    large_set: set[str],
    default_chunk_size: int,
    default_chunk_overlap: int,
    default_splitter: str,
    default_loader: str,
    image_based_loader: str,
    image_based_chunk_size: int,
    large_document_chunk_size: int,
    upload_settings: dict,
) -> list[dict]:
    """Build the list of loader entries for the output JSON.
    
    This function generates loader configurations based on whether a document
    is marked as image-based, large, or normal. The loader choice and chunk
    size are adjusted accordingly.
    """
    loader_list: list[dict] = []
    for name in name_list:
        curr_size = default_chunk_size
        curr_overlap = default_chunk_overlap
        curr_splitter = default_splitter
        curr_loader = default_loader
        if name in image_set and name not in large_set:
            curr_loader = image_based_loader
            curr_size = image_based_chunk_size
        elif name not in image_set and name in large_set:
            curr_size = large_document_chunk_size
        elif name in image_set and name in large_set:
            curr_loader = image_based_loader
        base_name = os.path.splitext(name)[0]
        path = name if folder_name == "null" else f"{folder_name}/{name}"
        loader_list.append(
            {
                "loader": curr_loader,
                "args": {"path": path, "start_page_num": 1},
                "splitter": curr_splitter,
                "splitter_args": {"chunk_size": curr_size, "chunk_overlap": curr_overlap},
                "metadata": {"title": base_name},
                "settings": {
                    "on_source_conflict": upload_settings.get("on_source_conflict", "OVERRIDE"),
                    "do_not_split": bool(upload_settings.get("do_not_split", False)),
                },
            }
        )
    return loader_list


def _runs_dir(upload_id: str) -> str:
    """Return the per-session runs directory path."""
    return os.path.join(RUNS_ROOT, upload_id)


def _validate_upload_id(upload_id: str) -> bool:
    """Check upload_id format to avoid traversal or malformed ids."""
    return bool(UPLOAD_ID_RE.match(upload_id))


def _safe_docs_basename(folder_name: str) -> str:
    """Return sanitized docs basename with 'docs' fallback for empty input.

    If the user provided a non-empty name, we sanitize it (which may become
    'file' depending on characters). If the user provided empty/whitespace,
    we fallback to 'docs'.
    """
    if not folder_name or not folder_name.strip():
        return "docs"
    return filename_checker.sanitize_basename(folder_name)


def generate_loader_names(
    selected_image_docs: list[str],
    selected_large_docs: list[str],
    name_list: list[str],
) -> tuple[set, set]:
    """Convert form input lists to sets for loader generation."""
    filtered_names = _filter_names_from_list(name_list)
    image_set_input = set(_filter_names_from_list(selected_image_docs))
    large_set_input = set(_filter_names_from_list(selected_large_docs))
    name_set = set(filtered_names)
    image_set = image_set_input & name_set
    large_set = large_set_input & name_set
    return image_set, large_set
