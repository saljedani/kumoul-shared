from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Folder, File, ActivityLog

folders_bp = Blueprint('folders', __name__)


@folders_bp.route('/folders/create', methods=['POST'])
@login_required
def create():
    name = request.form.get('name', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    dept = request.form.get('department', '')
    color = request.form.get('color', '#1a3a6b')

    if not name:
        flash('Folder name is required.', 'warning')
        return redirect(request.referrer or url_for('files.list_files'))

    folder = Folder(
        name=name,
        owner_id=current_user.id,
        parent_id=parent_id,
        department=dept,
        color=color
    )
    db.session.add(folder)
    db.session.commit()
    flash(f'Folder "{name}" created.', 'success')
    return redirect(url_for('files.list_files', folder_id=parent_id))


@folders_bp.route('/folders/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    if folder.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)
    parent_id = folder.parent_id
    db.session.delete(folder)
    db.session.commit()
    flash(f'Folder deleted.', 'success')
    return redirect(url_for('files.list_files', folder_id=parent_id))


@folders_bp.route('/files/<int:file_id>/move', methods=['POST'])
@login_required
def move_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)
    new_folder_id = request.form.get('folder_id', type=int)
    file.folder_id = new_folder_id
    db.session.commit()
    flash('File moved.', 'success')
    return redirect(request.referrer or url_for('files.list_files'))
