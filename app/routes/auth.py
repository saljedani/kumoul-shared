from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, ActivityLog
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=bool(remember))
            user.last_login = datetime.utcnow()
            log = ActivityLog(
                user_id=user.id,
                action='login',
                details=f'User logged in',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page or url_for('dashboard.home'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    log = ActivityLog(
        user_id=current_user.id,
        action='logout',
        details='User logged out',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            current_user.full_name = request.form.get('full_name', current_user.full_name)
            current_user.full_name_ar = request.form.get('full_name_ar', current_user.full_name_ar)
            current_user.email = request.form.get('email', current_user.email)
            current_user.theme = request.form.get('theme', current_user.theme)
            current_user.language = request.form.get('language', current_user.language)
            db.session.commit()
            flash('Profile updated successfully.', 'success')
        elif action == 'change_password':
            old_pw = request.form.get('old_password')
            new_pw = request.form.get('new_password')
            confirm_pw = request.form.get('confirm_password')
            if not current_user.check_password(old_pw):
                flash('Current password is incorrect.', 'danger')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
            elif len(new_pw) < 6:
                flash('Password must be at least 6 characters.', 'danger')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash('Password changed successfully.', 'success')
    return render_template('auth/profile.html')
