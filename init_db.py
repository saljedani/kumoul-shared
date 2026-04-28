"""
init_db.py — Initialize Kumoul SHARED database.
Run once after first install: python init_db.py
Safe to re-run: skips if data already exists.
"""

from app import create_app, db
from app.models import User, Folder, SharedFolder, Notification, DEPARTMENTS

app = create_app()

with app.app_context():
    print("Creating / updating all database tables …")
    db.create_all()   # creates new tables (shared_folders, shared_files) without dropping existing

    if User.query.first():
        print("Data already exists — skipping seed data.")
        print("  Tip: to reset, delete instance/kumoul.db and re-run.")
        exit(0)

    print("Seeding admin account …")
    admin = User(
        username='admin',
        email='admin@kumoul.com',
        full_name='System Administrator',
        full_name_ar='مدير النظام',
        department='Management',
        role='admin',
        avatar_color='#e85d04',
    )
    admin.set_password('Admin@123')
    db.session.add(admin)

    print("Seeding sample employees …")
    employees = [
        ('ahmed.rashidi',  'ahmed@kumoul.com',  'Ahmed Al-Rashidi', 'أحمد الراشدي', 'Engineering', '#1a3a6b'),
        ('fatima.malik',   'fatima@kumoul.com', 'Fatima Al-Malik',  'فاطمة المالك',  'HR',          '#2d6a4f'),
        ('omar.hassan',    'omar@kumoul.com',   'Omar Hassan',      'عمر حسن',       'Finance',     '#7b2d8b'),
        ('sara.ali',       'sara@kumoul.com',   'Sara Al-Ali',      'سارة العلي',    'Projects',    '#c1121f'),
        ('khalid.noor',    'khalid@kumoul.com', 'Khalid Noor',      'خالد نور',      'Management',  '#023e8a'),
    ]

    users = []
    for username, email, name, name_ar, dept, color in employees:
        u = User(username=username, email=email, full_name=name, full_name_ar=name_ar,
                 department=dept, role='employee', avatar_color=color)
        u.set_password('Employee@123')
        db.session.add(u)
        users.append(u)

    db.session.flush()

    print("Creating department folders …")
    dept_colors = {'HR':'#2d6a4f','Finance':'#7b2d8b','Projects':'#c1121f',
                   'Engineering':'#1a3a6b','Management':'#023e8a'}
    for dept in DEPARTMENTS[:-1]:
        db.session.add(Folder(
            name=dept, owner_id=admin.id, department=dept,
            is_department_folder=True, color=dept_colors.get(dept, '#1a3a6b'),
            description=f'{dept} department shared folder'))

    print("Creating default Shared Company File folders …")
    for fname, fcolor in [('General Announcements','#e85d04'),
                           ('Policies & Procedures','#1a3a6b'),
                           ('Templates','#2d6a4f')]:
        db.session.add(SharedFolder(name=fname, created_by=admin.id, color=fcolor))

    print("Sending welcome notifications …")
    for u in users:
        db.session.add(Notification(
            user_id=u.id,
            title='Welcome to Kumoul SHARED 🎉',
            message='Your account is ready. Check out the new Shared Company Files section!',
            type='announcement'))

    db.session.commit()

    print()
    print("=" * 55)
    print("  ✅  Database initialized successfully!")
    print("=" * 55)
    print()
    print("  ADMIN ACCOUNT")
    print("  ─────────────────────────────────────")
    print("  Username : admin")
    print("  Password : Admin@123")
    print()
    print("  SAMPLE EMPLOYEES  (password: Employee@123)")
    print("  ─────────────────────────────────────")
    for username, _, name, _, dept, _ in employees:
        print(f"  @{username:<18} {name}  ({dept})")
    print()
    print("  Run the app:  python run.py")
    print("  Visit:        http://localhost:5000")
    print("=" * 55)
