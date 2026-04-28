from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    full_name_ar = db.Column(db.String(150))
    department = db.Column(db.String(100), nullable=False, default='General')
    role = db.Column(db.String(20), nullable=False, default='employee')
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    avatar_color = db.Column(db.String(20), default='#1a3a6b')
    storage_used = db.Column(db.BigInteger, default=0)
    storage_limit = db.Column(db.BigInteger, default=5 * 1024 * 1024 * 1024)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    theme = db.Column(db.String(10), default='light')
    language = db.Column(db.String(5), default='en')

    files = db.relationship('File', backref='owner', lazy='dynamic', foreign_keys='File.owner_id')
    folders = db.relationship('Folder', backref='owner', lazy='dynamic', foreign_keys='Folder.owner_id')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    sent_shares = db.relationship('FileShare', backref='sender', lazy='dynamic', foreign_keys='FileShare.sender_id')
    received_shares = db.relationship('FileShare', backref='recipient', lazy='dynamic', foreign_keys='FileShare.recipient_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_initials(self):
        parts = self.full_name.split()
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[-1][0].upper()
        return self.full_name[:2].upper()

    def storage_percent(self):
        if self.storage_limit == 0:
            return 0
        return min(100, round((self.storage_used / self.storage_limit) * 100, 1))


DEPARTMENTS = ['HR', 'Finance', 'Projects', 'Engineering', 'Management', 'General']


class Folder(db.Model):
    __tablename__ = 'folders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    department = db.Column(db.String(100))
    is_department_folder = db.Column(db.Boolean, default=False)
    is_company_folder = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(500))
    color = db.Column(db.String(20), default='#1a3a6b')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    children = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    files = db.relationship('File', backref='folder', lazy='dynamic')

    def get_path(self):
        path = [self.name]
        current = self
        while current.parent_id:
            current = Folder.query.get(current.parent_id)
            if current:
                path.insert(0, current.name)
        return ' / '.join(path)


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(300), nullable=False)
    stored_name = db.Column(db.String(300), nullable=False, unique=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, default=0)
    file_type = db.Column(db.String(100))
    extension = db.Column(db.String(20))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    department = db.Column(db.String(100))
    description = db.Column(db.String(1000))
    is_company_wide = db.Column(db.Boolean, default=False)
    is_announcement = db.Column(db.Boolean, default=False)
    version = db.Column(db.Integer, default=1)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shares = db.relationship('FileShare', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='file', lazy='dynamic', cascade='all, delete-orphan')

    def human_size(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def icon_class(self):
        icons = {
            'pdf': 'bi-file-earmark-pdf-fill text-danger',
            'doc': 'bi-file-earmark-word-fill text-primary',
            'docx': 'bi-file-earmark-word-fill text-primary',
            'xls': 'bi-file-earmark-excel-fill text-success',
            'xlsx': 'bi-file-earmark-excel-fill text-success',
            'ppt': 'bi-file-earmark-ppt-fill text-warning',
            'pptx': 'bi-file-earmark-ppt-fill text-warning',
            'png': 'bi-file-earmark-image-fill text-info',
            'jpg': 'bi-file-earmark-image-fill text-info',
            'jpeg': 'bi-file-earmark-image-fill text-info',
            'gif': 'bi-file-earmark-image-fill text-info',
            'zip': 'bi-file-earmark-zip-fill text-secondary',
            'rar': 'bi-file-earmark-zip-fill text-secondary',
            'txt': 'bi-file-earmark-text-fill text-muted',
            'csv': 'bi-file-earmark-spreadsheet-fill text-success',
            'mp4': 'bi-file-earmark-play-fill',
            'mp3': 'bi-file-earmark-music-fill',
            'dwg': 'bi-file-earmark-code-fill',
        }
        return icons.get(self.extension.lower() if self.extension else '', 'bi-file-earmark-fill text-secondary')

    def is_previewable(self):
        return self.extension and self.extension.lower() in ['pdf', 'png', 'jpg', 'jpeg', 'gif']


class FileShare(db.Model):
    __tablename__ = 'file_shares'
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(500))
    can_download = db.Column(db.Boolean, default=True)
    is_viewed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)


class TeamFolder(db.Model):
    __tablename__ = 'team_folders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    department = db.Column(db.String(100))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(500))
    type = db.Column(db.String(50), default='info')
    link = db.Column(db.String(300))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    related_file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])


# ═══════════════════════════════════════════════════════════════
#   SHARED COMPANY FILES  —  visible to ALL logged-in employees
# ═══════════════════════════════════════════════════════════════

class SharedFolder(db.Model):
    """Folders inside the Shared Company Files space."""
    __tablename__ = 'shared_folders'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    parent_id   = db.Column(db.Integer, db.ForeignKey('shared_folders.id'), nullable=True)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    color       = db.Column(db.String(20), default='#1a3a6b')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    children = db.relationship(
        'SharedFolder',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    files   = db.relationship(
        'SharedFile', backref='folder', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    creator = db.relationship('User', foreign_keys=[created_by])

    def file_count(self):
        return self.files.count()

    def get_path(self):
        parts, cur = [self.name], self
        for _ in range(10):
            if not cur.parent_id:
                break
            cur = SharedFolder.query.get(cur.parent_id)
            if cur:
                parts.insert(0, cur.name)
        return ' / '.join(parts)


class SharedFile(db.Model):
    """Files in the Shared Company Files space."""
    __tablename__ = 'shared_files'

    id             = db.Column(db.Integer, primary_key=True)
    original_name  = db.Column(db.String(300), nullable=False)
    stored_name    = db.Column(db.String(300), nullable=False, unique=True)
    file_path      = db.Column(db.String(500), nullable=False)
    file_size      = db.Column(db.BigInteger, default=0)
    file_type      = db.Column(db.String(100))
    extension      = db.Column(db.String(20))
    uploaded_by    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    folder_id      = db.Column(db.Integer, db.ForeignKey('shared_folders.id'), nullable=True)
    description    = db.Column(db.String(1000))
    download_count = db.Column(db.Integer, default=0)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    uploader = db.relationship('User', foreign_keys=[uploaded_by])

    def human_size(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def icon_class(self):
        icons = {
            'pdf':  'bi-file-earmark-pdf-fill text-danger',
            'doc':  'bi-file-earmark-word-fill text-primary',
            'docx': 'bi-file-earmark-word-fill text-primary',
            'xls':  'bi-file-earmark-excel-fill text-success',
            'xlsx': 'bi-file-earmark-excel-fill text-success',
            'ppt':  'bi-file-earmark-ppt-fill text-warning',
            'pptx': 'bi-file-earmark-ppt-fill text-warning',
            'png':  'bi-file-earmark-image-fill text-info',
            'jpg':  'bi-file-earmark-image-fill text-info',
            'jpeg': 'bi-file-earmark-image-fill text-info',
            'gif':  'bi-file-earmark-image-fill text-info',
            'zip':  'bi-file-earmark-zip-fill text-secondary',
            'rar':  'bi-file-earmark-zip-fill text-secondary',
            'txt':  'bi-file-earmark-text-fill text-muted',
            'csv':  'bi-file-earmark-spreadsheet-fill text-success',
            'mp4':  'bi-file-earmark-play-fill',
            'mp3':  'bi-file-earmark-music-fill',
            'dwg':  'bi-file-earmark-code-fill',
        }
        return icons.get((self.extension or '').lower(), 'bi-file-earmark-fill text-secondary')

    def is_previewable(self):
        return (self.extension or '').lower() in ('pdf', 'png', 'jpg', 'jpeg', 'gif')
