"""Configuration and constants for the PDF processing app."""

from __future__ import annotations

import logging
import os
import re

from flask import Flask

import filename_checker

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# App configuration
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB
app.secret_key = os.environ.get("APP_SECRET_KEY", "dev-secret")

# Root directories
RUNS_ROOT = "runs"
UPLOAD_ROOT = "tmp_uploads"

# Default processing values
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_SPLITTER = "RecursiveCharacterTextSplitter"
DEFAULT_LOADER = "FileLoader"
IMAGE_BASED_LOADER = "DoclingFileLoader"
IMAGE_BASED_CHUNK_SIZE = 500
LARGE_DOCUMENT_CHUNK_SIZE = 2000

# Cleanup after 24 hours
MAX_AGE_SECONDS = 24 * 60 * 60

# New on_source_conflict options
ALLOWED_OSC = {"OVERRIDE", "RETAIN", "DUPLICATE", "RAISE ERROR"}
DEFAULT_UPLOAD_SETTINGS = {
    "on_source_conflict": "OVERRIDE",
    "do_not_split": False,
}

# Upload ID validation regex
UPLOAD_ID_RE = re.compile(r"^[a-f0-9]{32}$", re.IGNORECASE)
