"""
init_db.py — Initialize Kumoul SHARED database with sample data.
Run once: python init_db.py
"""

from app import create_app, db
from app.models import User, Folder, File, Notification, DEPARTMENTS
import os

app = create_app()

with app.app_context():
    print("Creating database tables...")
    db.create_all()

    # Check if already initialized
    if User.query.first():
        print("Database already initialized. Skipping.")
        exit(0)

    print("Creating admin account...")
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

    print("Creating sample employees...")
    employees = [
        ('ahmed.rashidi', 'ahmed@kumoul.com', 'Ahmed Al-Rashidi', 'أحمد الراشدي', 'Engineering', '#1a3a6b'),
        ('fatima.malik', 'fatima@kumoul.com', 'Fatima Al-Malik', 'فاطمة المالك', 'HR', '#2d6a4f'),
        ('omar.hassan', 'omar@kumoul.com', 'Omar Hassan', 'عمر حسن', 'Finance', '#7b2d8b'),
        ('sara.ali', 'sara@kumoul.com', 'Sara Al-Ali', 'سارة العلي', 'Projects', '#c1121f'),
        ('khalid.noor', 'khalid@kumoul.com', 'Khalid Noor', 'خالد نور', 'Management', '#023e8a'),
    ]

    users = []
    for username, email, name, name_ar, dept, color in employees:
        u = User(
            username=username,
            email=email,
            full_name=name,
            full_name_ar=name_ar,
            department=dept,
            role='employee',
            avatar_color=color,
        )
        u.set_password('Employee@123')
        db.session.add(u)
        users.append(u)

    db.session.flush()

    print("Creating department folders...")
    dept_colors = {
        'HR': '#2d6a4f',
        'Finance': '#7b2d8b',
        'Projects': '#c1121f',
        'Engineering': '#1a3a6b',
        'Management': '#023e8a',
    }

    for dept in DEPARTMENTS[:-1]:  # skip General
        folder = Folder(
            name=dept,
            owner_id=admin.id,
            department=dept,
            is_department_folder=True,
            color=dept_colors.get(dept, '#1a3a6b'),
            description=f'{dept} department shared folder'
        )
        db.session.add(folder)

    print("Creating welcome notification...")
    for user in users:
        notif = Notification(
            user_id=user.id,
            title='Welcome to Kumoul SHARED! 🎉',
            message='Your account is ready. Upload files, share with colleagues, and collaborate easily.',
            type='announcement'
        )
        db.session.add(notif)

    db.session.commit()
    print("\n✅ Database initialized successfully!")
    print("=" * 50)
    print("ADMIN ACCOUNT:")
    print("  Username: admin")
    print("  Password: Admin@123")
    print("\nSAMPLE EMPLOYEES (all use password: Employee@123):")
    for username, email, name, _, dept, _ in employees:
        print(f"  @{username} — {name} ({dept})")
    print("=" * 50)
    print("\nRun the app: python run.py")
