from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import File, User, FileShare, Notification

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    dept = request.args.get('dept', '')
    file_type = request.args.get('type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    owner = request.args.get('owner', '')

    results = []
    if q or dept or file_type or date_from or owner:
        query = db.session.query(File, User).join(User, File.owner_id == User.id)

        # Access filter: own files + shared with me + company wide + dept files
        from sqlalchemy import or_
        shared_file_ids = db.session.query(FileShare.file_id).filter_by(
            recipient_id=current_user.id
        ).subquery()

        query = query.filter(
            or_(
                File.owner_id == current_user.id,
                File.id.in_(shared_file_ids),
                File.is_company_wide == True,
                File.department == current_user.department,
                current_user.role == 'admin'
            )
        )

        if q:
            query = query.filter(
                File.original_name.ilike(f'%{q}%') |
                File.description.ilike(f'%{q}%') |
                User.full_name.ilike(f'%{q}%') |
                User.username.ilike(f'%{q}%')
            )
        if dept:
            query = query.filter(File.department == dept)
        if file_type:
            query = query.filter(File.extension.ilike(f'%{file_type}%'))
        if date_from:
            from datetime import datetime
            try:
                query = query.filter(File.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
            except:
                pass
        if date_to:
            from datetime import datetime
            try:
                query = query.filter(File.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
            except:
                pass
        if owner:
            query = query.filter(User.username.ilike(f'%{owner}%') | User.full_name.ilike(f'%{owner}%'))

        results = query.order_by(File.created_at.desc()).limit(50).all()

    from app.models import DEPARTMENTS
    return render_template('files/search.html',
        results=results, q=q, dept=dept, file_type=file_type,
        date_from=date_from, date_to=date_to, owner=owner,
        departments=DEPARTMENTS
    )


# ---- Notifications ----
notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/notifications')
@login_required
def list_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(50).all()
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('dashboard/notifications.html', notifications=notifs)


@notifications_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})


@notifications_bp.route('/api/notifications/unread')
@login_required
def unread_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    recent = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(5).all()
    return jsonify({
        'count': count,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'link': n.link or '#',
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%b %d, %H:%M')
        } for n in recent]
    })
