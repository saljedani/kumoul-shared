from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()


db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY', 'kumoul-shared-secret-key-2024-change-in-production'
    )

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(app.instance_path, 'kumoul.db')
    )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['UPLOAD_FOLDER'] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'uploads'
    )

    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    app.config['WTF_CSRF_ENABLED'] = True

    app.config['ALLOWED_EXTENSIONS'] = {
        'pdf','png','jpg','jpeg','gif','doc','docx','xls','xlsx',
        'ppt','pptx','txt','csv','zip','rar','7z','mp4','avi',
        'mp3','dwg','dxf','step','iges','stl'
    }

    # AWS S3
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
    app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
    app.config['AWS_BUCKET_NAME'] = os.getenv('AWS_BUCKET_NAME')
    app.config['AWS_REGION'] = os.getenv('AWS_REGION')
    if config:
        app.config.update(config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.files import files_bp
    from app.routes.folders import folders_bp
    from app.routes.sharing import sharing_bp
    from app.routes.admin import admin_bp
    from app.routes.search import search_bp, notifications_bp
    from app.routes.company import company_bp

    for bp in (
        auth_bp, dashboard_bp, files_bp, folders_bp,
        sharing_bp, admin_bp, search_bp,
        notifications_bp, company_bp
    ):
        app.register_blueprint(bp)

    @app.template_global('format_bytes')
    def _format_bytes(value):
        return fmt_bytes(value)

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        unread = 0
        if current_user.is_authenticated:
            from app.models import Notification
            unread = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()

        return dict(unread_notifications=unread)

    return app


def fmt_bytes(size):
    if not size:
        return '0 B'

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} TB"


format_bytes_util = fmt_bytes