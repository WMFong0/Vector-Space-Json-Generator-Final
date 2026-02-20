
from __future__ import annotations
import json, os, zipfile, uuid, shutil
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, get_flashed_messages
import filename_checker

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.secret_key = 'dev-secret'

OUTPUT_PATH = 'output.txt'
OUTPUT_PATH2 = 'output2.txt'
UPLOAD_ROOT = 'tmp_uploads'

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_SPLITTER = 'RecursiveCharacterTextSplitter'
DEFAULT_LOADER = 'FileLoader'
IMAGE_BASED_LOADER = 'DoclingFileLoader'
IMAGE_BASED_CHUNK_SIZE = 500
LARGE_DOCUMENT_CHUNK_SIZE = 2000

DEFAULT_UPLOAD_SETTINGS = {
    'on_source_conflict': 'OVERRIDE',
    'do_not_split': False,
}

# As we limits user to input .pdf file, a just incase method to force naming all files .pdf
def _allowed_file(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] == '.pdf'

# Function renaming
def _sanitize_zip_name(filename: str) -> str:
    return filename_checker.sanitize_filename(filename)


def _dedupe_zip_name(name: str, seen: set) -> str:
    if name not in seen:
        seen.add(name); return name
    base, ext = os.path.splitext(name)
    i = 2
    while f"{base}-{i}{ext}" in seen:
        i += 1
    cand = f"{base}-{i}{ext}"
    seen.add(cand)
    return cand

# as name induced, fix naming of files inside folder
def _filter_names_from_list(names):
    out = []
    for line in names:
        if not line: continue
        base, ext = os.path.splitext(line)
        safe_base = filename_checker.filter_name(base)
        if safe_base is not None:
            out.append(f"{safe_base}{ext}")
    return out

# Generate JSON settings files
def _generate_loaders(name_list, folder_name, image_set, large_set,
                       default_chunk_size, default_chunk_overlap,
                       default_splitter, default_loader,
                       image_based_loader, image_based_chunk_size,
                       large_document_chunk_size,
                       upload_settings: dict):
    loader_list = []
    for name in name_list:
        curr_size = default_chunk_size
        curr_overlap = default_chunk_overlap
        curr_splitter = default_splitter
        curr_loader = default_loader
        if name in image_set and name not in large_set:
            curr_loader = image_based_loader; curr_size = image_based_chunk_size
        elif name not in image_set and name in large_set:
            curr_size = large_document_chunk_size
        elif name in image_set and name in large_set:
            curr_loader = image_based_loader
        base_name = os.path.splitext(name)[0]
        loader_list.append({
            'loader': curr_loader,
            'args': {'path': f"{folder_name}/{name}", 'start_page_num': 1},
            'splitter': curr_splitter,
            'splitter_args': {'chunk_size': curr_size, 'chunk_overlap': curr_overlap},
            'metadata': {'title': base_name},
            'settings': {
                'on_source_conflict': upload_settings.get('on_source_conflict', 'OVERRIDE'),
                'do_not_split': bool(upload_settings.get('do_not_split', False)),
            }
        })
    return loader_list

# Redirect home page to upload
@app.route('/')
def home():
    return redirect(url_for('upload'))

# Upload Page
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    errors = []
    if request.method == 'POST':
        pdf_files = request.files.getlist('pdf_files')
        valid = [f for f in pdf_files if f and f.filename and _allowed_file(f.filename)]
        if not valid:
            errors.append('Please upload at least one PDF file.')
        else:
            upload_id = uuid.uuid4().hex
            upload_dir = os.path.join(UPLOAD_ROOT, upload_id)
            os.makedirs(upload_dir, exist_ok=True)
            mapping = {}
            for f in valid:
                stored = _sanitize_zip_name(f.filename)
                with open(os.path.join(upload_dir, stored), 'wb') as fh:
                    fh.write(f.read())
                mapping[stored] = f.filename
            with open(os.path.join(upload_dir, 'metadata.json'), 'w', encoding='utf-8') as meta:
                json.dump(mapping, meta)
            return redirect(url_for('mark', upload_id=upload_id))
    return render_template('upload.html', errors=errors)

# Settings Page
@app.route('/mark/<upload_id>', methods=['GET', 'POST'])
def mark(upload_id):
    errors = []
    warnings = []
    for cat, msg in get_flashed_messages(with_categories=True):
        if cat == 'error': errors.append(msg)
        elif cat == 'warning': warnings.append(msg)

    upload_dir = os.path.join(UPLOAD_ROOT, upload_id)
    meta_path = os.path.join(upload_dir, 'metadata.json')
    if not os.path.exists(meta_path):
        errors.append('Upload session not found. Please re-upload your files.')
        return render_template('upload.html', errors=errors), 400
    with open(meta_path, 'r', encoding='utf-8') as fh:
        mapping = json.load(fh)
    pdf_names = list(mapping.values())

    form_defaults = {
        'folder_name': '',
        'default_chunk_size': str(DEFAULT_CHUNK_SIZE),
        'default_chunk_overlap': str(DEFAULT_CHUNK_OVERLAP),
        'default_splitter': DEFAULT_SPLITTER,
        'default_loader': DEFAULT_LOADER,
        'image_based_loader': IMAGE_BASED_LOADER,
        'image_based_chunk_size': str(IMAGE_BASED_CHUNK_SIZE),
        'large_document_chunk_size': str(LARGE_DOCUMENT_CHUNK_SIZE),
        'on_source_conflict': DEFAULT_UPLOAD_SETTINGS['on_source_conflict'],
        'do_not_split': 'false' if not DEFAULT_UPLOAD_SETTINGS['do_not_split'] else 'true',
    }

    selected_image_docs = []
    selected_large_docs = []
    settings_text = ''

    if request.method == 'POST':
        selected_image_docs = request.form.getlist('image_docs')
        selected_large_docs = request.form.getlist('large_docs')
        form_defaults.update({
            'folder_name': request.form.get('folder_name', '').strip(),
            'default_chunk_size': request.form.get('default_chunk_size', str(DEFAULT_CHUNK_SIZE)),
            'default_chunk_overlap': request.form.get('default_chunk_overlap', str(DEFAULT_CHUNK_OVERLAP)),
            'default_splitter': request.form.get('default_splitter', DEFAULT_SPLITTER),
            'default_loader': request.form.get('default_loader', DEFAULT_LOADER),
            'image_based_loader': request.form.get('image_based_loader', IMAGE_BASED_LOADER),
            'image_based_chunk_size': request.form.get('image_based_chunk_size', str(IMAGE_BASED_CHUNK_SIZE)),
            'large_document_chunk_size': request.form.get('large_document_chunk_size', str(LARGE_DOCUMENT_CHUNK_SIZE)),
            'on_source_conflict': request.form.get('on_source_conflict', DEFAULT_UPLOAD_SETTINGS['on_source_conflict']).strip() or DEFAULT_UPLOAD_SETTINGS['on_source_conflict'],
            'do_not_split': request.form.get('do_not_split', 'false'),
        })
        settings_text = request.form.get('settings_text', '').strip()
        if not form_defaults['folder_name']:
            errors.append('Folder name is required.')
        if not pdf_names:
            errors.append('No PDFs found for this session.')
        if not errors:
            return redirect(url_for('generate', upload_id=upload_id))

    return render_template('mark.html',
                           upload_id=upload_id,
                           pdf_names=pdf_names,
                           selected_image_docs=selected_image_docs,
                           selected_large_docs=selected_large_docs,
                           settings_text=settings_text,
                           errors=errors,
                           warnings=warnings,
                           **form_defaults)

# Generate JSON file and Result page
@app.route('/generate/<upload_id>', methods=['GET', 'POST'])
def generate(upload_id):
    upload_dir = os.path.join(UPLOAD_ROOT, upload_id)
    meta_path = os.path.join(upload_dir, 'metadata.json')
    if not os.path.exists(meta_path):
        flash('Upload session not found. Please re-upload your files.', 'error')
        return redirect(url_for('mark', upload_id=upload_id))
    with open(meta_path, 'r', encoding='utf-8') as fh:
        mapping = json.load(fh)
    pdf_names = list(mapping.values())

    if request.method == 'GET':
        flash('Please submit your selections from the previous page to generate outputs.', 'warning')
        return redirect(url_for('mark', upload_id=upload_id))

    selected_image_docs = request.form.getlist('image_docs')
    selected_large_docs = request.form.getlist('large_docs')

    folder_name = request.form.get('folder_name', '').strip()
    default_chunk_size = request.form.get('default_chunk_size', str(DEFAULT_CHUNK_SIZE))
    default_chunk_overlap = request.form.get('default_chunk_overlap', str(DEFAULT_CHUNK_OVERLAP))
    default_splitter = request.form.get('default_splitter', DEFAULT_SPLITTER)
    default_loader = request.form.get('default_loader', DEFAULT_LOADER)
    image_based_loader = request.form.get('image_based_loader', IMAGE_BASED_LOADER)
    image_based_chunk_size = request.form.get('image_based_chunk_size', str(IMAGE_BASED_CHUNK_SIZE))
    large_document_chunk_size = request.form.get('large_document_chunk_size', str(LARGE_DOCUMENT_CHUNK_SIZE))
    on_source_conflict = request.form.get('on_source_conflict', DEFAULT_UPLOAD_SETTINGS['on_source_conflict']).strip() or DEFAULT_UPLOAD_SETTINGS['on_source_conflict']
    do_not_split = request.form.get('do_not_split', 'false')
    settings_text = request.form.get('settings_text', '').strip()

    if not folder_name:
        flash('Folder name is required.', 'error')
    if not pdf_names:
        flash('No PDFs found for this session.', 'error')

    try:
        default_chunk_size = int(default_chunk_size)
        default_chunk_overlap = int(default_chunk_overlap)
        image_based_chunk_size = int(image_based_chunk_size)
        large_document_chunk_size = int(large_document_chunk_size)
    except ValueError:
        flash('Chunk sizes and overlap must be integers.', 'error')
        default_chunk_size = DEFAULT_CHUNK_SIZE
        default_chunk_overlap = DEFAULT_CHUNK_OVERLAP
        image_based_chunk_size = IMAGE_BASED_CHUNK_SIZE
        large_document_chunk_size = LARGE_DOCUMENT_CHUNK_SIZE

    cats_msgs = get_flashed_messages(with_categories=True)
    if any(cat == 'error' for cat, _ in cats_msgs):
        for cat, msg in cats_msgs:
            flash(msg, cat)
        return redirect(url_for('mark', upload_id=upload_id))

    settings = None
    if settings_text:
        try:
            data = json.loads(settings_text)
            settings = data.get('settings') if isinstance(data, dict) else None
        except (json.JSONDecodeError, ValueError) as exc:
            flash(f'Ignoring pasted settings (invalid JSON): {exc}', 'warning')

    filtered_names = _filter_names_from_list(pdf_names)
    output2_text = ''.join(filtered_names) + ('' if filtered_names else '')
    with open(OUTPUT_PATH2, 'w', encoding='utf-8') as fh:
        fh.write(output2_text)

    upload_settings = {
        'on_source_conflict': on_source_conflict,
        'do_not_split': (do_not_split == 'true'),
    }
    name_set = set(filtered_names)
    image_set_input = set(_filter_names_from_list(selected_image_docs))
    large_set_input = set(_filter_names_from_list(selected_large_docs))
    image_set = image_set_input & name_set
    large_set = large_set_input & name_set

    loaders = _generate_loaders(
        filtered_names,
        folder_name,
        image_set, large_set,
        default_chunk_size, default_chunk_overlap,
        default_splitter, default_loader,
        image_based_loader, image_based_chunk_size,
        large_document_chunk_size,
        upload_settings,
    )
    data_final = {
        'settings': settings or {
            'on_source_conflict': upload_settings['on_source_conflict'],
            'do_not_split': upload_settings['do_not_split']
        },
        'common_args': {},
        'loaders': loaders,
    }
    output_json = json.dumps(data_final, indent=4)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as fh:
        fh.write(output_json)

    safe_docs_name = filename_checker.sanitize_basename(folder_name) or 'docs'
    zip_filename = f"{safe_docs_name}.zip"
    try:
        seen = set()
        with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for stored in os.listdir(upload_dir):
                if not stored.lower().endswith('.pdf'):
                    continue
                original = mapping.get(stored, stored)
                zip_name = _sanitize_zip_name(original)
                zip_name = _dedupe_zip_name(zip_name, seen)
                with open(os.path.join(upload_dir, stored), 'rb') as fh:
                    zipf.writestr(zip_name, fh.read())
        zip_ready = True
    except OSError as exc:
        flash(f'Failed to create zip: {exc}', 'warning')
        zip_ready = False

    try:
        shutil.rmtree(upload_dir)
    except OSError:
        pass

    result = {
        'filtered_names': filtered_names,
        'output_json': output_json,
        'output2_text': output2_text,
        'zip_ready': zip_ready,
        'zip_filename': zip_filename,
    }

    return render_template('result.html', errors=[], warnings=get_flashed_messages(), result=result)

@app.route('/download/<name>')
def download(name: str):
    if name == 'output':
        path = OUTPUT_PATH
    elif name == 'output2':
        path = OUTPUT_PATH2
    elif name == 'zip':
        fname = request.args.get('fname')
        path = fname if fname else 'output_pdfs.zip' # Usually else case won't run as we requires user to input folder name
    else:
        path = None
    if not path:
        return ('Not found', 404)
    if not os.path.exists(path):
        return ('File not found. Generate outputs first.', 404)
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
