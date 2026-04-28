from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import SharedFolder, SharedFile
from app.s3_utils import upload_file, get_url, delete_file
from datetime import datetime

company_bp = Blueprint('company', __name__, url_prefix='/company')


@company_bp.route('/')
@login_required
def index():
    folder_id = request.args.get('folder_id', type=int)
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    sort = request.args.get('sort', 'newest')

    folder_query = SharedFolder.query.filter_by(parent_id=folder_id)
    file_query = SharedFile.query.filter_by(folder_id=folder_id)

    if q:
        folder_query = folder_query.filter(
            SharedFolder.name.ilike(f"%{q}%")
        )
        file_query = file_query.filter(
            SharedFile.original_name.ilike(f"%{q}%")
        )

    if sort == 'oldest':
        file_query = file_query.order_by(SharedFile.created_at.asc())
    elif sort == 'name':
        file_query = file_query.order_by(SharedFile.original_name.asc())
    elif sort == 'size':
        file_query = file_query.order_by(SharedFile.file_size.desc())
    else:
        file_query = file_query.order_by(SharedFile.created_at.desc())

    folders = folder_query.all()
    files = file_query.paginate(page=page, per_page=20, error_out=False)

    total_files = SharedFile.query.count()
    total_folders = SharedFolder.query.count()
    total_bytes = db.session.query(
        db.func.sum(SharedFile.file_size)
    ).scalar() or 0

    current_folder = SharedFolder.query.get(folder_id) if folder_id else None
    all_folders = SharedFolder.query.all()

    return render_template(
        'company/index.html',
        folders=folders,
        files=files,
        current_folder=current_folder,
        breadcrumb=[],
        q=q,
        sort=sort,
        total_files=total_files,
        total_folders=total_folders,
        total_bytes=total_bytes,
        all_folders=all_folders
    )


@company_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    folder_id = request.form.get('folder_id', type=int)
    description = request.form.get('description', '')
    uploaded = 0

    for f in request.files.getlist('files'):
        if not f or not f.filename:
            continue
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)

        key = upload_file(f)
        ext = f.filename.rsplit('.', 1)[1].lower() if '.' in f.filename else ''

        item = SharedFile(
            original_name=f.filename,
            stored_name=key,
            file_path=key,
            file_size=size,
            file_type=f.content_type,
            extension=ext,
            uploaded_by=current_user.id,
            folder_id=folder_id,
            description=description,
            download_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.session.add(item)
        uploaded += 1

    db.session.commit()

    flash(f'{uploaded} file(s) uploaded.', 'success')
    return redirect(url_for('company.index', folder_id=folder_id))


@company_bp.route('/download/<int:file_id>')
@login_required
def download(file_id):
    file = SharedFile.query.get_or_404(file_id)
    file.download_count += 1
    db.session.commit()
    return redirect(get_url(file.file_path))


@company_bp.route('/preview/<int:file_id>')
@login_required
def preview(file_id):
    file = SharedFile.query.get_or_404(file_id)
    return redirect(get_url(file.file_path))


@company_bp.route('/folder/create', methods=['POST'])
@login_required
def create_folder():
    name = request.form.get('name')
    parent_id = request.form.get('parent_id', type=int)
    color = request.form.get('color', '#1a3a6b')

    if name:
        folder = SharedFolder(
            name=name,
            parent_id=parent_id,
            created_by=current_user.id,
            color=color,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(folder)
        db.session.commit()

    return redirect(url_for('company.index', folder_id=parent_id))


@company_bp.route('/folder/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete_folder(folder_id):
    folder = SharedFolder.query.get_or_404(folder_id)
    db.session.delete(folder)
    db.session.commit()
    flash('Folder deleted.', 'success')
    return redirect(url_for('company.index'))


@company_bp.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file_route(file_id):
    file = SharedFile.query.get_or_404(file_id)
    delete_file(file.file_path)
    db.session.delete(file)
    db.session.commit()
    flash('File deleted.', 'success')
    return redirect(url_for('company.index'))


@company_bp.route('/folder/<int:folder_id>/rename', methods=['POST'])
@login_required
def rename_folder(folder_id):
    folder = SharedFolder.query.get_or_404(folder_id)
    folder.name = request.form.get('name')
    folder.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('company.index', folder_id=folder.parent_id))


@company_bp.route('/file/<int:file_id>/rename', methods=['POST'])
@login_required
def rename_file(file_id):
    file = SharedFile.query.get_or_404(file_id)
    file.original_name = request.form.get('name')
    file.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('company.index', folder_id=file.folder_id))


@company_bp.route('/file/<int:file_id>/move', methods=['POST'])
@login_required
def move_file(file_id):
    file = SharedFile.query.get_or_404(file_id)
    new_folder_id = request.form.get('folder_id', type=int)
    file.folder_id = new_folder_id
    file.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('company.index', folder_id=new_folder_id))