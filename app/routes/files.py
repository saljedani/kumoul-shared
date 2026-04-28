from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.models import File, Folder, ActivityLog, Notification, User
from werkzeug.utils import secure_filename
from app.s3_utils import upload_file, get_url, delete_file
import uuid
from datetime import datetime

files_bp = Blueprint('files', __name__)


def allowed_file(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def get_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


@files_bp.route('/files')
@login_required
def list_files():
    folder_id = request.args.get('folder_id', type=int)
    dept = request.args.get('dept')
    page = request.args.get('page', 1, type=int)

    query = File.query.filter_by(owner_id=current_user.id)

    if folder_id:
        query = query.filter_by(folder_id=folder_id)
        current_folder = Folder.query.get_or_404(folder_id)
    else:
        current_folder = None
        if not dept:
            query = query.filter_by(folder_id=None)

    if dept:
        query = File.query.filter_by(department=dept)

    files = query.order_by(File.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    if folder_id:
        folders = Folder.query.filter_by(owner_id=current_user.id, parent_id=folder_id).all()
    else:
        folders = Folder.query.filter_by(owner_id=current_user.id, parent_id=None).all()

    return render_template(
        'files/list.html',
        files=files,
        folders=folders,
        current_folder=current_folder,
        dept=dept
    )


@files_bp.route('/files/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        folder_id = request.form.get('folder_id', type=int)
        dept = request.form.get('department', current_user.department)
        description = request.form.get('description', '')
        is_company_wide = request.form.get('is_company_wide') == 'on'
        is_announcement = request.form.get('is_announcement') == 'on'

        if current_user.role != 'admin':
            is_announcement = False

        uploaded_files = request.files.getlist('files')
        success_count = 0

        for up in uploaded_files:
            if up and up.filename and allowed_file(up.filename):
                ext = get_extension(up.filename)
                key = upload_file(up)

                new_file = File(
                    original_name=up.filename,
                    stored_name=key,
                    file_path=key,
                    file_size=up.content_length or 0,
                    file_type=up.content_type,
                    extension=ext,
                    owner_id=current_user.id,
                    folder_id=folder_id,
                    department=dept,
                    description=description,
                    is_company_wide=is_company_wide,
                    is_announcement=is_announcement
                )

                db.session.add(new_file)

                log = ActivityLog(
                    user_id=current_user.id,
                    action='upload',
                    details=f'Uploaded: {up.filename}',
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                success_count += 1

        db.session.commit()

        if success_count:
            flash(f'{success_count} file(s) uploaded successfully!', 'success')
        else:
            flash('No valid files uploaded.', 'warning')

        return redirect(url_for('files.list_files', folder_id=folder_id))

    folder_id = request.args.get('folder_id', type=int)
    folders = Folder.query.filter_by(owner_id=current_user.id).all()
    return render_template('files/upload.html', folders=folders, folder_id=folder_id)


@files_bp.route('/files/<int:file_id>/download')
@login_required
def download(file_id):
    file = File.query.get_or_404(file_id)

    if file.owner_id != current_user.id and current_user.role != 'admin':
        from app.models import FileShare
        share = FileShare.query.filter_by(file_id=file_id, recipient_id=current_user.id).first()
        if not share and not file.is_company_wide and file.department != current_user.department:
            abort(403)

    file.download_count += 1
    db.session.commit()

    return redirect(get_url(file.file_path))


@files_bp.route('/files/<int:file_id>/preview')
@login_required
def preview(file_id):
    file = File.query.get_or_404(file_id)
    return redirect(get_url(file.file_path))


@files_bp.route('/files/<int:file_id>/delete', methods=['POST'])
@login_required
def delete(file_id):
    file = File.query.get_or_404(file_id)

    if file.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)

    folder_id = file.folder_id

    delete_file(file.file_path)
    db.session.delete(file)
    db.session.commit()

    flash('File deleted.', 'success')
    return redirect(url_for('files.list_files', folder_id=folder_id))


@files_bp.route('/files/<int:file_id>/view')
@login_required
def view_file(file_id):
    file = File.query.get_or_404(file_id)
    return render_template('files/view.html', file=file)


@files_bp.route('/files/<int:file_id>/replace', methods=['POST'])
@login_required
def replace(file_id):
    file = File.query.get_or_404(file_id)

    if file.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)

    new_file = request.files.get('new_file')
    if not new_file or not new_file.filename:
        flash('No file selected.', 'warning')
        return redirect(url_for('files.view_file', file_id=file_id))

    delete_file(file.file_path)

    key = upload_file(new_file)
    ext = get_extension(new_file.filename)

    file.stored_name = key
    file.file_path = key
    file.file_type = new_file.content_type
    file.extension = ext
    file.version += 1
    file.updated_at = datetime.utcnow()

    db.session.commit()

    flash(f'File replaced (version {file.version}).', 'success')
    return redirect(url_for('files.view_file', file_id=file_id))