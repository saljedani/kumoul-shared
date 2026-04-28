"""
migrate_company.py
──────────────────
Run this ONCE on an EXISTING Kumoul SHARED installation
to add the new shared_folders and shared_files tables.

  python migrate_company.py

Safe to run multiple times — uses CREATE TABLE IF NOT EXISTS.
"""
from app import create_app, db
from app.models import SharedFolder, SharedFile

app = create_app()
with app.app_context():
    db.create_all()   # only creates missing tables, leaves existing data alone
    print("✅  shared_folders and shared_files tables created (if they didn't exist).")

    # Optionally seed a couple of default folders
    if not SharedFolder.query.first():
        from app.models import User
        admin = User.query.filter_by(role='admin').first()
        if admin:
            for name, color in [('General Announcements','#e85d04'),
                                 ('Policies & Procedures','#1a3a6b'),
                                 ('Templates','#2d6a4f')]:
                db.session.add(SharedFolder(name=name, created_by=admin.id, color=color))
            db.session.commit()
            print("✅  Default Company File folders seeded.")
    print("Done. Restart your Flask app.")
