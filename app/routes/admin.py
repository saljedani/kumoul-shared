from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, File, ActivityLog, Notification, FileShare, DEPARTMENTS
from functools import wraps
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users = User.query.filter_by(is_active=True).count()
    total_files = File.query.count()
    total_storage = db.session.query(db.func.sum(File.file_size)).scalar() or 0
    total_shares = FileShare.query.count()
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(20).all()
    users = User.query.order_by(User.created_at.desc()).all()

    dept_stats = db.session.query(
        File.department, db.func.count(File.id)
    ).group_by(File.department).all()

    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_files=total_files,
        total_storage=total_storage,
        total_shares=total_shares,
        recent_logs=recent_logs,
        users=users,
        dept_stats=dept_stats
    )


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        dept = request.form.get('department', 'General')
        role = request.form.get('role', 'employee')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        else:
            colors = ['#1a3a6b', '#e85d04', '#2d6a4f', '#7b2d8b', '#c1121f', '#023e8a']
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                department=dept,
                role=role,
                avatar_color=colors[User.query.count() % len(colors)]
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f'User {username} created successfully.', 'success')
            return redirect(url_for('admin.dashboard'))

    return render_template('admin/create_user.html', departments=DEPARTMENTS)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate your own account.', 'warning')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.username} {status}.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_pw = request.form.get('password', '')
    if len(new_pw) < 6:
        flash('Password must be at least 6 characters.', 'danger')
    else:
        user.set_password(new_pw)
        db.session.commit()
        flash(f'Password reset for {user.username}.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/broadcast', methods=['POST'])
@login_required
@admin_required
def broadcast():
    title = request.form.get('title', '').strip()
    message = request.form.get('message', '').strip()
    if not title or not message:
        flash('Title and message required.', 'warning')
        return redirect(url_for('admin.dashboard'))

    all_users = User.query.filter(User.id != current_user.id, User.is_active == True).all()
    for u in all_users:
        notif = Notification(
            user_id=u.id,
            title=f'📢 {title}',
            message=message,
            type='announcement'
        )
        db.session.add(notif)
    db.session.commit()
    flash(f'Broadcast sent to {len(all_users)} users.', 'success')
    return redirect(url_for('admin.dashboard'))
