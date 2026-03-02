"""Three-phase PDF processing web app with hardened IO and logging.

Phases:
 1) /upload   – upload PDFs (session created)
 2) /mark     – mark image-based / large docs + set options
 3) /generate – build outputs per session and offer downloads

Features:
 - Session-based processing with UUID-based upload IDs
 - File sanitization via filename_checker module
 - Security: isolated runs per session, no path traversal
 - Fixed loader/splitter settings (display-only, not editable)
 - Supports both image-based and large-document processing
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import uuid
import zipfile
from flask import (
    Flask,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from config import app, logger, RUNS_ROOT, ALLOWED_OSC, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_SPLITTER, DEFAULT_LOADER, IMAGE_BASED_CHUNK_SIZE, IMAGE_BASED_LOADER, LARGE_DOCUMENT_CHUNK_SIZE, DEFAULT_UPLOAD_SETTINGS, UPLOAD_ID_RE, UPLOAD_ROOT
from helpers import (
    _allowed_file,
    _sanitize_zip_name,
    _dedupe_zip_name,
    _filter_names_from_list,
    _cleanup_old_sessions,
    _generate_loaders,
    _runs_dir,
    _validate_upload_id,
    _safe_docs_basename,
    generate_loader_names,
)

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------

@app.route("/health")
def health_check():
    """Return health status."""
    return {"status": "healthy"}


@app.route("/")
def home():
    """Redirect to the upload page."""
    return redirect(url_for("upload"))


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """Step 1: Upload PDFs and create a new session (upload_id)."""
    errors: list[str] = []
    if request.method == "POST":
        pdf_files = request.files.getlist("pdf_files")
        valid = [f for f in pdf_files if f and f.filename and _allowed_file(f.filename)]
        if not valid:
            errors.append("Please upload at least one PDF file.")
        else:
            upload_id = uuid.uuid4().hex
            upload_dir = os.path.join(UPLOAD_ROOT, upload_id)
            os.makedirs(upload_dir, exist_ok=True)
            mapping: dict[str, str] = {}
            for f in valid:
                stored = _sanitize_zip_name(f.filename)
                dest = os.path.join(upload_dir, stored)
                f.save(dest)
                mapping[stored] = f.filename
            meta_path = os.path.join(upload_dir, "metadata.json")
            with open(meta_path, "w", encoding="utf-8") as meta:
                json.dump(mapping, meta)
            logger.info("Upload created: upload_id=%s files=%d", upload_id, len(valid))
            _cleanup_old_sessions()
            return redirect(url_for("mark", upload_id=upload_id))
    return render_template("upload.html", errors=errors)


@app.route("/mark/<upload_id>", methods=["GET", "POST"])
def mark(upload_id: str):
    """Step 2: Mark docs and configure options for a given session.
    
    This route renders the configuration page and handles form submissions.
    It now uses a combined single-row layout for both image-based and large
    document checkboxes for each file.
    """
    if not _validate_upload_id(upload_id):
        logger.warning("Invalid upload_id on /mark: %s", upload_id)
        return ("Invalid session id.", 400)

    errors: list[str] = []
    warnings: list[str] = []

    for cat, msg in get_flashed_messages(with_categories=True):
        if cat == "error":
            errors.append(msg)
        elif cat == "warning":
            warnings.append(msg)

    upload_dir = os.path.join(UPLOAD_ROOT, upload_id)
    meta_path = os.path.join(upload_dir, "metadata.json")
    if not os.path.exists(meta_path):
        errors.append("Upload session not found. Please re-upload your files.")
        return render_template("upload.html", errors=errors), 400

    with open(meta_path, "r", encoding="utf-8") as fh:
        mapping = json.load(fh)
    pdf_names = list(mapping.values())

    form_defaults = {
        "folder_name": "",
        "default_chunk_size": str(DEFAULT_CHUNK_SIZE),
        "default_chunk_overlap": str(DEFAULT_CHUNK_OVERLAP),
        "default_splitter": DEFAULT_SPLITTER,
        "default_loader": DEFAULT_LOADER,
        "image_based_loader": IMAGE_BASED_LOADER,
        "image_based_chunk_size": str(IMAGE_BASED_CHUNK_SIZE),
        "large_document_chunk_size": str(LARGE_DOCUMENT_CHUNK_SIZE),
        "on_source_conflict": DEFAULT_UPLOAD_SETTINGS["on_source_conflict"],
        "do_not_split": "false" if not DEFAULT_UPLOAD_SETTINGS["do_not_split"] else "true",
    }

    selected_image_docs: list[str] = []
    selected_large_docs: list[str] = []
    settings_text = ""

    if request.method == "POST":
        selected_image_docs = request.form.getlist("image_docs")
        selected_large_docs = request.form.getlist("large_docs")
        form_defaults.update(
            {
                "folder_name": request.form.get("folder_name", "").strip(),
                "default_chunk_size": request.form.get("default_chunk_size", str(DEFAULT_CHUNK_SIZE)),
                "default_chunk_overlap": request.form.get("default_chunk_overlap", str(DEFAULT_CHUNK_OVERLAP)),
                "default_splitter": request.form.get("default_splitter", DEFAULT_SPLITTER),
                "default_loader": request.form.get("default_loader", DEFAULT_LOADER),
                "image_based_loader": request.form.get("image_based_loader", IMAGE_BASED_LOADER),
                "image_based_chunk_size": request.form.get("image_based_chunk_size", str(IMAGE_BASED_CHUNK_SIZE)),
                "large_document_chunk_size": request.form.get("large_document_chunk_size", str(LARGE_DOCUMENT_CHUNK_SIZE)),
                "on_source_conflict": request.form.get("on_source_conflict", DEFAULT_UPLOAD_SETTINGS["on_source_conflict"]).strip()
                or DEFAULT_UPLOAD_SETTINGS["on_source_conflict"],
                "do_not_split": request.form.get("do_not_split", "false"),
            }
        )
        settings_text = request.form.get("settings_text", "").strip()

        if not form_defaults["folder_name"]:
            errors.append("Folder name is required.")
        if not pdf_names:
            errors.append("No PDFs found for this session.")
        if not errors:
            _cleanup_old_sessions()
            return redirect(url_for("generate", upload_id=upload_id))

    return render_template(
        "mark.html",
        upload_id=upload_id,
        pdf_names=pdf_names,
        selected_image_docs=selected_image_docs,
        selected_large_docs=selected_large_docs,
        settings_text=settings_text,
        errors=errors,
        warnings=warnings,
        **form_defaults,
    )


@app.route("/generate/<upload_id>", methods=["GET", "POST"])
def generate(upload_id: str):
    """Step 3: Generate outputs for a given session and render results.
    
    This route processes form data, validates inputs, and generates:
    - output.json: Vector space processing configuration
    - output2.txt: Sanitized filenames list
    - .zip file: Original PDFs packaged together
    
    The checkbox layout has been changed to single-row per file (image-based
    and large checkboxes on same row) but form handling remains unchanged.
    """
    if not _validate_upload_id(upload_id):
        logger.warning("Invalid upload_id on /generate: %s", upload_id)
        return redirect(url_for("mark", upload_id=upload_id))

    upload_dir = os.path.join(UPLOAD_ROOT, upload_id)
    meta_path = os.path.join(upload_dir, "metadata.json")
    if not os.path.exists(meta_path):
        flash("Upload session not found. Please re-upload your files.", "error")
        return redirect(url_for("mark", upload_id=upload_id))

    with open(meta_path, "r", encoding="utf-8") as fh:
        mapping: dict[str, str] = json.load(fh)
    pdf_names = list(mapping.values())

    if request.method == "GET":
        flash("Please submit your selections from the previous page to generate outputs.", "warning")
        return redirect(url_for("mark", upload_id=upload_id))

    # Collect form fields
    selected_image_docs = request.form.getlist("image_docs")
    selected_large_docs = request.form.getlist("large_docs")

    folder_name_in = request.form.get("folder_name", "")
    folder_name = folder_name_in.strip()
    default_chunk_size = request.form.get("default_chunk_size", str(DEFAULT_CHUNK_SIZE))
    default_chunk_overlap = request.form.get("default_chunk_overlap", str(DEFAULT_CHUNK_OVERLAP))
    default_splitter = request.form.get("default_splitter", DEFAULT_SPLITTER)
    default_loader = request.form.get("default_loader", DEFAULT_LOADER)
    image_based_loader = request.form.get("image_based_loader", IMAGE_BASED_LOADER)
    image_based_chunk_size = request.form.get("image_based_chunk_size", str(IMAGE_BASED_CHUNK_SIZE))
    large_document_chunk_size = request.form.get("large_document_chunk_size", str(LARGE_DOCUMENT_CHUNK_SIZE))
    on_source_conflict = request.form.get("on_source_conflict", DEFAULT_UPLOAD_SETTINGS["on_source_conflict"]).strip() or DEFAULT_UPLOAD_SETTINGS["on_source_conflict"]
    do_not_split = request.form.get("do_not_split", "false")
    settings_text = request.form.get("settings_text", "").strip()

    # Basic validations
    if not folder_name:
        flash("Folder name is required.", "error")
    if not pdf_names:
        flash("No PDFs found for this session.", "error")

    # Parse numeric fields
    try:
        default_chunk_size = int(default_chunk_size)
        default_chunk_overlap = int(default_chunk_overlap)
        image_based_chunk_size = int(image_based_chunk_size)
        large_document_chunk_size = int(large_document_chunk_size)
    except ValueError:
        flash("Chunk sizes and overlap must be integers.", "error")
        default_chunk_size = DEFAULT_CHUNK_SIZE
        default_chunk_overlap = DEFAULT_CHUNK_OVERLAP
        image_based_chunk_size = IMAGE_BASED_CHUNK_SIZE
        large_document_chunk_size = LARGE_DOCUMENT_CHUNK_SIZE

    # Numeric constraints
    if default_chunk_size <= 0:
        flash("Default chunk size must be > 0.", "error")
    if not (0 <= default_chunk_overlap < default_chunk_size):
        flash("Default chunk overlap must be between 0 and chunk size - 1.", "error")
    if image_based_chunk_size <= 0 or large_document_chunk_size <= 0:
        flash("Chunk sizes must be > 0.", "error")

    # on_source_conflict whitelist
    if on_source_conflict not in ALLOWED_OSC:
        flash("Invalid on_source_conflict option.", "error")

    # If any error was flashed, bounce back to mark
    cats_msgs = get_flashed_messages(with_categories=True)
    if any(cat == "error" for cat, _ in cats_msgs):
        for cat, msg in cats_msgs:
            flash(msg, cat)
        return redirect(url_for("mark", upload_id=upload_id))

    # Optional settings JSON parsing
    settings = None
    if settings_text:
        try:
            data = json.loads(settings_text)
            settings = data.get("settings") if isinstance(data, dict) else None
        except (json.JSONDecodeError, ValueError) as exc:
            flash(f"Ignoring pasted settings (invalid JSON): {exc}", "warning")

    # Prepare outputs dir: runs/<upload_id>/
    run_dir = _runs_dir(upload_id)
    os.makedirs(run_dir, exist_ok=True)

    # Filter names
    filtered_names = _filter_names_from_list(pdf_names)

    # output2.txt (sanitized names list)
    output2_path = os.path.join(run_dir, "output2.txt")
    output2_text = "".join(filtered_names) + ("\n" if filtered_names else "")
    with open(output2_path, "w", encoding="utf-8") as fh:
        fh.write(output2_text)

    # Build JSON data
    upload_settings = {
        "on_source_conflict": on_source_conflict,
        "do_not_split": (do_not_split == "true"),
    }
    image_set, large_set = generate_loader_names(selected_image_docs, selected_large_docs, pdf_names)

    loaders = _generate_loaders(
        filtered_names,
        _safe_docs_basename(folder_name),
        image_set,
        large_set,
        default_chunk_size,
        default_chunk_overlap,
        default_splitter,
        default_loader,
        image_based_loader,
        image_based_chunk_size,
        large_document_chunk_size,
        upload_settings,
    )

    data_final = {
        "settings": settings
        or {
            "on_source_conflict": upload_settings["on_source_conflict"],
            "do_not_split": upload_settings["do_not_split"],
        },
        "common_args": {},
        "loaders": loaders,
    }

    output_json_path = os.path.join(run_dir, "output.json")
    with open(output_json_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data_final, indent=4))

    # Build ZIP (streamed); name based on folder_name (with fallback rule)
    safe_docs_name = "output" if folder_name == "null" else _safe_docs_basename(folder_name)
    zip_filename = f"{safe_docs_name}.zip"
    zip_path = os.path.join(run_dir, zip_filename)
    try:
        seen: set[str] = set()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for stored in os.listdir(upload_dir):
                if not stored.lower().endswith('.pdf'):
                    continue
                original = mapping.get(stored, stored)
                zip_name = _sanitize_zip_name(original)
                zip_name = _dedupe_zip_name(zip_name, seen)
                file_path = os.path.join(upload_dir, stored)
                zipf.write(file_path, arcname=zip_name)
        zip_ready = True
    except OSError as exc:
        logger.exception("Failed to create zip for upload_id=%s: %s", upload_id, exc)
        flash(f"Failed to create zip: {exc}", "warning")
        zip_ready = False

    # Cleanup upload temp dir (not the runs dir)
    try:
        shutil.rmtree(upload_dir)
    except OSError:
        logger.warning("Failed to remove upload temp dir: %s", upload_dir)

    result = {
        "filtered_names": filtered_names,
        "output_json": json.dumps(data_final, indent=4),
        "output2_text": output2_text,
        "zip_ready": zip_ready,
        "zip_filename": zip_filename,
    }
    logger.info("Generated outputs for upload_id=%s -> %s", upload_id, run_dir)
    _cleanup_old_sessions()
    return render_template("result.html", errors=[], warnings=get_flashed_messages(), result=result, upload_id=upload_id)


@app.route("/download/<upload_id>/<name>")
def download(upload_id: str, name: str):
    """Serve per-session outputs safely.

    Parameters
    ----------
    upload_id: str
        Session identifier (UUID hex without dashes).
    name: str
        One of: 'output' | 'output2' | 'zip'
    """
    if not _validate_upload_id(upload_id):
        logger.warning("Invalid upload_id on /download: %s", upload_id)
        return ("Invalid session id.", 400)

    run_dir = _runs_dir(upload_id)
    if not os.path.isdir(run_dir):
        return ("Session outputs not found.", 404)

    if name == "output":
        path = os.path.join(run_dir, "output.json")
        mimetype = "application/json"
        dl_name = "output.json"
    elif name == "output2":
        path = os.path.join(run_dir, "output2.txt")
        mimetype = "text/plain"
        dl_name = "output2.txt"
    elif name == "zip":
        # There should be exactly one .zip we produced – find it.
        zips = [p for p in os.listdir(run_dir) if p.lower().endswith('.zip')]
        if not zips:
            return ("ZIP not found for session.", 404)
        path = os.path.join(run_dir, zips[0])
        mimetype = "application/zip"
        dl_name = zips[0]
    else:
        return ("Not found", 404)

    if not os.path.exists(path):
        return ("File not found. Generate outputs first.", 404)
    return send_file(path, as_attachment=True, download_name=dl_name, mimetype=mimetype)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
