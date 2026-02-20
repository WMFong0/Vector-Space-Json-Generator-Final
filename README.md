
# Backend — All Fixes (session-safe outputs, secure downloads, logging)

## What’s fixed
- Per-session outputs under `runs/<upload_id>/` (no cross-session overwrite).
- Secure downloads at `/download/<upload_id>/<name>` (no arbitrary paths).
- JSON file consistently named **output.json** (served with `application/json`).
- ZIP creation streams from disk (`zipfile.ZipFile.write`), avoiding RAM spikes.
- Server-side validation for `on_source_conflict` and numeric fields.
- Clipboard **Copy JSON** includes a legacy fallback if Clipboard API is blocked.
- Detailed **logging** and docstrings for maintainability.

## Run
```bash
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```
