from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
from datetime import timedelta

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Default config
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kumoul-shared-secret-key-2024-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(app.instance_path, 'kumoul.db')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['ALLOWED_EXTENSIONS'] = {
        'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx',
        'ppt', 'pptx', 'txt', 'csv', 'zip', 'rar', '7z', 'mp4', 'avi',
        'mp3', 'dwg', 'dxf', 'step', 'iges', 'stl'
    }

    if config:
        app.config.update(config)

    # Ensure instance and upload folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.files import files_bp
    from app.routes.folders import folders_bp
    from app.routes.sharing import sharing_bp
    from app.routes.admin import admin_bp
    from app.routes.search import search_bp
    from app.routes.search import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(folders_bp)
    app.register_blueprint(sharing_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(notifications_bp)


    # Jinja2 global helper
    @app.template_global('format_bytes')
    def format_bytes_global(value):
        return format_bytes_util(value)

    # Context processor for global template vars
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        unread_count = 0
        if current_user.is_authenticated:
            from app.models import Notification
            unread_count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
        return dict(unread_notifications=unread_count)

    return app

# Standalone utility (also used in init)
def format_bytes_util(size):
    if not size:
        return '0 B'
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
