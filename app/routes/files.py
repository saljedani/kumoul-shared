from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.models import File, Folder, ActivityLog, Notification, User
from werkzeug.utils import secure_filename
import os
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

    # User's folders
    if folder_id:
        folders = Folder.query.filter_by(owner_id=current_user.id, parent_id=folder_id).all()
    else:
        folders = Folder.query.filter_by(owner_id=current_user.id, parent_id=None).all()

    return render_template('files/list.html',
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

        for upload_file in uploaded_files:
            if upload_file and upload_file.filename and allowed_file(upload_file.filename):
                original_name = secure_filename(upload_file.filename)
                ext = get_extension(original_name)
                stored_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)

                upload_file.save(file_path)
                file_size = os.path.getsize(file_path)

                new_file = File(
                    original_name=upload_file.filename,
                    stored_name=stored_name,
                    file_path=file_path,
                    file_size=file_size,
                    file_type=upload_file.content_type,
                    extension=ext,
                    owner_id=current_user.id,
                    folder_id=folder_id,
                    department=dept,
                    description=description,
                    is_company_wide=is_company_wide,
                    is_announcement=is_announcement,
                )
                db.session.add(new_file)
                current_user.storage_used += file_size

                log = ActivityLog(
                    user_id=current_user.id,
                    action='upload',
                    details=f'Uploaded: {upload_file.filename}',
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                success_count += 1

                # Notify dept members if dept file
                if dept and dept != 'General':
                    dept_users = User.query.filter(
                        User.department == dept,
                        User.id != current_user.id,
                        User.is_active == True
                    ).all()
                    for u in dept_users:
                        notif = Notification(
                            user_id=u.id,
                            title='New department file',
                            message=f'{current_user.full_name} uploaded "{upload_file.filename}" to {dept}',
                            type='info',
                            link=url_for('files.list_files', dept=dept)
                        )
                        db.session.add(notif)

                # Company-wide announcement
                if is_announcement:
                    all_users = User.query.filter(User.id != current_user.id, User.is_active == True).all()
                    for u in all_users:
                        notif = Notification(
                            user_id=u.id,
                            title='📢 Company Announcement',
                            message=f'New announcement: "{upload_file.filename}"',
                            type='announcement',
                            link=url_for('files.list_files')
                        )
                        db.session.add(notif)

        db.session.commit()

        if success_count > 0:
            flash(f'{success_count} file(s) uploaded successfully!', 'success')
        else:
            flash('No valid files were uploaded.', 'warning')

        return redirect(url_for('files.list_files', folder_id=folder_id))

    folder_id = request.args.get('folder_id', type=int)
    folders = Folder.query.filter_by(owner_id=current_user.id).all()
    return render_template('files/upload.html', folders=folders, folder_id=folder_id)


@files_bp.route('/files/<int:file_id>/download')
@login_required
def download(file_id):
    file = File.query.get_or_404(file_id)

    # Check permission
    if file.owner_id != current_user.id and current_user.role != 'admin':
        # Check if shared
        from app.models import FileShare
        share = FileShare.query.filter_by(file_id=file_id, recipient_id=current_user.id).first()
        if not share and not file.is_company_wide and file.department != current_user.department:
            abort(403)

    file.download_count += 1
    log = ActivityLog(
        user_id=current_user.id,
        file_id=file_id,
        action='download',
        details=f'Downloaded: {file.original_name}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return send_file(file.file_path, download_name=file.original_name, as_attachment=True)


@files_bp.route('/files/<int:file_id>/preview')
@login_required
def preview(file_id):
    file = File.query.get_or_404(file_id)
    if not file.is_previewable():
        flash('This file type cannot be previewed.', 'warning')
        return redirect(url_for('files.list_files'))

    # Permission check
    if file.owner_id != current_user.id and current_user.role != 'admin':
        from app.models import FileShare
        share = FileShare.query.filter_by(file_id=file_id, recipient_id=current_user.id).first()
        if not share and not file.is_company_wide:
            abort(403)

    return send_file(file.file_path, mimetype=file.file_type)


@files_bp.route('/files/<int:file_id>/delete', methods=['POST'])
@login_required
def delete(file_id):
    file = File.query.get_or_404(file_id)

    if file.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)

    folder_id = file.folder_id
    current_user.storage_used = max(0, current_user.storage_used - file.file_size)

    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception:
        pass

    log = ActivityLog(
        user_id=current_user.id,
        action='delete',
        details=f'Deleted: {file.original_name}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.delete(file)
    db.session.commit()

    flash(f'"{file.original_name}" has been deleted.', 'success')
    return redirect(url_for('files.list_files', folder_id=folder_id))


@files_bp.route('/files/<int:file_id>/view')
@login_required
def view_file(file_id):
    file = File.query.get_or_404(file_id)

    # Permission check
    can_view = (
        file.owner_id == current_user.id or
        current_user.role == 'admin' or
        file.is_company_wide or
        file.department == current_user.department
    )
    if not can_view:
        from app.models import FileShare
        share = FileShare.query.filter_by(file_id=file_id, recipient_id=current_user.id).first()
        if not share:
            abort(403)

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

    # Remove old
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception:
        pass

    old_size = file.file_size
    ext = get_extension(new_file.filename)
    stored_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)
    new_file.save(file_path)
    new_size = os.path.getsize(file_path)

    file.stored_name = stored_name
    file.file_path = file_path
    file.file_size = new_size
    file.file_type = new_file.content_type
    file.extension = ext
    file.version += 1
    file.updated_at = datetime.utcnow()

    current_user.storage_used = max(0, current_user.storage_used - old_size + new_size)
    db.session.commit()

    flash(f'File replaced (version {file.version}).', 'success')
    return redirect(url_for('files.view_file', file_id=file_id))
