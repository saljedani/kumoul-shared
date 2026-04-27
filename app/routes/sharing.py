from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import FileShare, File, User, Notification, ActivityLog

sharing_bp = Blueprint('sharing', __name__)


@sharing_bp.route('/share/<int:file_id>', methods=['POST'])
@login_required
def share_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)

    recipient_username = request.form.get('recipient', '').strip()
    message = request.form.get('message', '')

    recipient = User.query.filter(
        (User.username == recipient_username) | (User.email == recipient_username)
    ).first()

    if not recipient:
        flash(f'User "{recipient_username}" not found.', 'danger')
        return redirect(request.referrer or url_for('files.list_files'))

    if recipient.id == current_user.id:
        flash('You cannot share a file with yourself.', 'warning')
        return redirect(request.referrer or url_for('files.list_files'))

    # Check duplicate
    existing = FileShare.query.filter_by(
        file_id=file_id, sender_id=current_user.id, recipient_id=recipient.id
    ).first()
    if existing:
        flash(f'File already shared with {recipient.full_name}.', 'info')
        return redirect(request.referrer or url_for('files.list_files'))

    share = FileShare(
        file_id=file_id,
        sender_id=current_user.id,
        recipient_id=recipient.id,
        message=message
    )
    db.session.add(share)

    notif = Notification(
        user_id=recipient.id,
        title='File Shared With You',
        message=f'{current_user.full_name} shared "{file.original_name}" with you' + (f': {message}' if message else ''),
        type='share',
        link=url_for('sharing.shared_with_me'),
        related_file_id=file_id
    )
    db.session.add(notif)

    log = ActivityLog(
        user_id=current_user.id,
        file_id=file_id,
        action='share',
        details=f'Shared with {recipient.username}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    flash(f'File shared with {recipient.full_name}!', 'success')
    return redirect(request.referrer or url_for('files.list_files'))


@sharing_bp.route('/shared/with-me')
@login_required
def shared_with_me():
    page = request.args.get('page', 1, type=int)
    shares = db.session.query(FileShare, File, User).join(
        File, FileShare.file_id == File.id
    ).join(User, FileShare.sender_id == User.id).filter(
        FileShare.recipient_id == current_user.id
    ).order_by(FileShare.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    # Mark as viewed
    FileShare.query.filter_by(recipient_id=current_user.id, is_viewed=False).update({'is_viewed': True})
    db.session.commit()

    return render_template('shared/with_me.html', shares=shares)


@sharing_bp.route('/shared/by-me')
@login_required
def shared_by_me():
    page = request.args.get('page', 1, type=int)
    shares = db.session.query(FileShare, File, User).join(
        File, FileShare.file_id == File.id
    ).join(User, FileShare.recipient_id == User.id).filter(
        FileShare.sender_id == current_user.id
    ).order_by(FileShare.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template('shared/by_me.html', shares=shares)


@sharing_bp.route('/share/revoke/<int:share_id>', methods=['POST'])
@login_required
def revoke_share(share_id):
    share = FileShare.query.get_or_404(share_id)
    if share.sender_id != current_user.id and current_user.role != 'admin':
        abort(403)
    db.session.delete(share)
    db.session.commit()
    flash('Share access revoked.', 'success')
    return redirect(url_for('sharing.shared_by_me'))


@sharing_bp.route('/api/users/search')
@login_required
def search_users():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    users = User.query.filter(
        User.is_active == True,
        User.id != current_user.id,
        (User.username.ilike(f'%{q}%') | User.full_name.ilike(f'%{q}%') | User.email.ilike(f'%{q}%'))
    ).limit(8).all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'full_name': u.full_name,
        'department': u.department,
        'initials': u.get_initials()
    } for u in users])
