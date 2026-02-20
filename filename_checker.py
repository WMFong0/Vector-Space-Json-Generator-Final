
from __future__ import annotations
import os, re
_ALLOWED = re.compile(r"[A-Za-z0-9_-]")
_SEP = "_"

def sanitize_basename(name: str) -> str:
    if name is None:
        return 'file'
    out = [ch if _ALLOWED.match(ch) else _SEP for ch in str(name)]
    import re as _r
    collapsed = _r.sub(r"_+", "_", ''.join(out)).strip('_')
    return collapsed or 'file'

def sanitize_filename(filename: str) -> str:
    base, ext = os.path.splitext(os.path.basename(filename or ''))
    return f"{sanitize_basename(base)}{ext}"

def filter_name(original_name: str) -> str | None:
    if not original_name:
        return None
    return sanitize_basename(original_name)
