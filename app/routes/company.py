"""
app/routes/company.py  —  Shared Company Files
"""
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, send_file, abort, jsonify, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import SharedFolder, SharedFile, Notification, User, ActivityLog
import os, uuid
from datetime import datetime

company_bp = Blueprint('company', __name__, url_prefix='/company')

def _allowed(fn):
    ext = fn.rsplit('.', 1)[1].lower() if '.' in fn else ''
    return ext in current_app.config['ALLOWED_EXTENSIONS']

def _ext(fn):
    return fn.rsplit('.', 1)[1].lower() if '.' in fn else ''

def _can_manage(item):
    owner = getattr(item, 'created_by', None) or getattr(item, 'uploaded_by', None)
    return current_user.id == owner or current_user.role == 'admin'

def _notify_all(title, message, link):
    for u in User.query.filter(User.id != current_user.id, User.is_active == True).all():
        db.session.add(Notification(user_id=u.id, title=title,
                                    message=message, type='info', link=link))

def _build_breadcrumb(folder):
    if not folder:
        return []
    crumbs, cur = [], folder
    for _ in range(10):
        crumbs.insert(0, {'name': cur.name, 'id': cur.id})
        if not cur.parent_id:
            break
        cur = SharedFolder.query.get(cur.parent_id)
        if not cur:
            break
    return crumbs

def _del_folder_recursive(folder):
    for child in folder.children.all():
        _del_folder_recursive(child)
    for f in folder.files.all():
        try:
            if os.path.exists(f.file_path):
                os.remove(f.file_path)
        except Exception:
            pass

# ── INDEX ──────────────────────────────────────────────────────────────────────
@company_bp.route('/')
@login_required
def index():
    folder_id = request.args.get('folder_id', type=int)
    q         = request.args.get('q', '').strip()
    sort      = request.args.get('sort', 'newest')
    page      = request.args.get('page', 1, type=int)
    current_folder = SharedFolder.query.get(folder_id) if folder_id else None

    folder_q = SharedFolder.query.filter_by(parent_id=folder_id)
    if q:
        folder_q = folder_q.filter(SharedFolder.name.ilike(f'%{q}%'))
    folders = folder_q.order_by(SharedFolder.name).all()

    file_q = SharedFile.query.filter_by(folder_id=folder_id)
    if q:
        file_q = file_q.filter(
            SharedFile.original_name.ilike(f'%{q}%') |
            SharedFile.description.ilike(f'%{q}%'))
    order = {'newest': SharedFile.created_at.desc(), 'oldest': SharedFile.created_at.asc(),
             'name': SharedFile.original_name.asc(), 'size': SharedFile.file_size.desc()}
    files = file_q.order_by(order.get(sort, SharedFile.created_at.desc()))\
                  .paginate(page=page, per_page=24, error_out=False)

    total_files   = SharedFile.query.count()
    total_folders = SharedFolder.query.count()
    total_bytes   = db.session.query(db.func.sum(SharedFile.file_size)).scalar() or 0
    breadcrumb    = _build_breadcrumb(current_folder)
    all_folders   = SharedFolder.query.order_by(SharedFolder.name).all()

    return render_template('company/index.html',
        folders=folders, files=files, current_folder=current_folder,
        breadcrumb=breadcrumb, q=q, sort=sort,
        total_files=total_files, total_folders=total_folders,
        total_bytes=total_bytes, all_folders=all_folders)

# ── UPLOAD ─────────────────────────────────────────────────────────────────────
@company_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    folder_id   = request.form.get('folder_id', type=int)
    description = request.form.get('description', '').strip()
    count = 0
    for f in request.files.getlist('files'):
        if not f or not f.filename:
            continue
        if not _allowed(f.filename):
            flash(f'"{f.filename}" — file type not allowed.', 'warning')
            continue
        ext    = _ext(f.filename)
        stored = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
        path   = os.path.join(current_app.config['UPLOAD_FOLDER'], stored)
        f.save(path)
        db.session.add(SharedFile(
            original_name=f.filename, stored_name=stored, file_path=path,
            file_size=os.path.getsize(path), file_type=f.content_type,
            extension=ext, uploaded_by=current_user.id,
            folder_id=folder_id, description=description))
        db.session.add(ActivityLog(user_id=current_user.id, action='company_upload',
            details=f'Company upload: {f.filename}', ip_address=request.remote_addr))
        count += 1
    if count:
        _notify_all('📁 New Company File',
            f'{current_user.full_name} uploaded {count} file(s) to Shared Company Files.',
            url_for('company.index', folder_id=folder_id or ''))
        db.session.commit()
        flash(f'{count} file(s) uploaded to Shared Company Files.', 'success')
    else:
        flash('No valid files uploaded.', 'warning')
    return redirect(url_for('company.index', folder_id=folder_id or ''))

# ── DOWNLOAD ───────────────────────────────────────────────────────────────────
@company_bp.route('/download/<int:file_id>')
@login_required
def download(file_id):
    sf = SharedFile.query.get_or_404(file_id)
    sf.download_count += 1
    db.session.add(ActivityLog(user_id=current_user.id, action='company_download',
        details=f'Downloaded: {sf.original_name}', ip_address=request.remote_addr))
    db.session.commit()
    return send_file(sf.file_path, download_name=sf.original_name, as_attachment=True)

# ── PREVIEW ────────────────────────────────────────────────────────────────────
@company_bp.route('/preview/<int:file_id>')
@login_required
def preview(file_id):
    sf = SharedFile.query.get_or_404(file_id)
    if not sf.is_previewable():
        abort(415)
    return send_file(sf.file_path, mimetype=sf.file_type or 'application/octet-stream')

# ── CREATE FOLDER ──────────────────────────────────────────────────────────────
@company_bp.route('/folder/create', methods=['POST'])
@login_required
def create_folder():
    name      = request.form.get('name', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    color     = request.form.get('color', '#1a3a6b')
    if not name:
        flash('Folder name is required.', 'warning')
        return redirect(url_for('company.index', folder_id=parent_id))
    if SharedFolder.query.filter_by(name=name, parent_id=parent_id).first():
        flash(f'A folder named "{name}" already exists here.', 'warning')
        return redirect(url_for('company.index', folder_id=parent_id))
    db.session.add(SharedFolder(name=name, parent_id=parent_id,
                                created_by=current_user.id, color=color))
    db.session.commit()
    flash(f'Folder "{name}" created.', 'success')
    return redirect(url_for('company.index', folder_id=parent_id))

# ── RENAME FOLDER ──────────────────────────────────────────────────────────────
@company_bp.route('/folder/<int:folder_id>/rename', methods=['POST'])
@login_required
def rename_folder(folder_id):
    sf = SharedFolder.query.get_or_404(folder_id)
    if not _can_manage(sf):
        abort(403)
    name = request.form.get('name', '').strip()
    if name:
        sf.name = name
        db.session.commit()
        flash('Folder renamed.', 'success')
    return redirect(url_for('company.index', folder_id=sf.parent_id))

# ── DELETE FOLDER ──────────────────────────────────────────────────────────────
@company_bp.route('/folder/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete_folder(folder_id):
    sf = SharedFolder.query.get_or_404(folder_id)
    if not _can_manage(sf):
        abort(403)
    parent_id = sf.parent_id
    _del_folder_recursive(sf)
    db.session.delete(sf)
    db.session.commit()
    flash('Folder deleted.', 'success')
    return redirect(url_for('company.index', folder_id=parent_id))

# ── RENAME FILE ────────────────────────────────────────────────────────────────
@company_bp.route('/file/<int:file_id>/rename', methods=['POST'])
@login_required
def rename_file(file_id):
    sf = SharedFile.query.get_or_404(file_id)
    if not _can_manage(sf):
        abort(403)
    name = request.form.get('name', '').strip()
    if name:
        sf.original_name = name
        db.session.commit()
        flash('File renamed.', 'success')
    return redirect(url_for('company.index', folder_id=sf.folder_id))

# ── DELETE FILE ────────────────────────────────────────────────────────────────
@company_bp.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    sf = SharedFile.query.get_or_404(file_id)
    if not _can_manage(sf):
        abort(403)
    folder_id = sf.folder_id
    try:
        if os.path.exists(sf.file_path):
            os.remove(sf.file_path)
    except Exception:
        pass
    db.session.add(ActivityLog(user_id=current_user.id, action='company_delete',
        details=f'Deleted company file: {sf.original_name}', ip_address=request.remote_addr))
    db.session.delete(sf)
    db.session.commit()
    flash(f'"{sf.original_name}" deleted.', 'success')
    return redirect(url_for('company.index', folder_id=folder_id))

# ── MOVE FILE ──────────────────────────────────────────────────────────────────
@company_bp.route('/file/<int:file_id>/move', methods=['POST'])
@login_required
def move_file(file_id):
    sf = SharedFile.query.get_or_404(file_id)
    if not _can_manage(sf):
        abort(403)
    new_folder = request.form.get('folder_id', type=int)
    sf.folder_id = new_folder
    db.session.commit()
    flash('File moved.', 'success')
    return redirect(url_for('company.index', folder_id=new_folder))
