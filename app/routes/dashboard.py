from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import File, FileShare, Notification, ActivityLog, User, Folder
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def home():
    # Recent files (own)
    recent_files = File.query.filter_by(owner_id=current_user.id)\
        .order_by(File.created_at.desc()).limit(8).all()

    # Files shared with me today
    today = datetime.utcnow().date()
    shared_today = FileShare.query.filter(
        FileShare.recipient_id == current_user.id,
        func.date(FileShare.created_at) == today
    ).count()

    # Total files
    total_files = File.query.filter_by(owner_id=current_user.id).count()

    # Shared by me
    shared_by_me = FileShare.query.filter_by(sender_id=current_user.id).count()

    # Recent activity
    recent_activity = ActivityLog.query.filter_by(user_id=current_user.id)\
        .order_by(ActivityLog.created_at.desc()).limit(10).all()

    # Company announcements
    announcements = File.query.filter_by(is_announcement=True)\
        .order_by(File.created_at.desc()).limit(5).all()

    # Recently shared with me
    recent_shares = db.session.query(FileShare, File, User).join(
        File, FileShare.file_id == File.id
    ).join(User, FileShare.sender_id == User.id).filter(
        FileShare.recipient_id == current_user.id
    ).order_by(FileShare.created_at.desc()).limit(5).all()

    # Department files (same dept)
    dept_files = File.query.filter_by(department=current_user.department)\
        .order_by(File.created_at.desc()).limit(6).all() if current_user.department != 'General' else []

    return render_template('dashboard/home.html',
        recent_files=recent_files,
        shared_today=shared_today,
        total_files=total_files,
        shared_by_me=shared_by_me,
        recent_activity=recent_activity,
        announcements=announcements,
        recent_shares=recent_shares,
        dept_files=dept_files
    )


@dashboard_bp.route('/api/toggle-theme', methods=['POST'])
@login_required
def toggle_theme():
    current_user.theme = 'dark' if current_user.theme == 'light' else 'light'
    db.session.commit()
    return jsonify({'theme': current_user.theme})
