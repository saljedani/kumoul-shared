# Kumoul SHARED — Internal File Sharing Platform
### Kumoul Engineering Consulting

A production-ready, secure internal file sharing and collaboration platform for office use.

---

## 📋 Features

| Feature | Details |
|---|---|
| **Authentication** | Login, logout, session timeout, password hashing (bcrypt) |
| **Role-based Access** | Admin & Employee roles with permission checks |
| **File Upload** | Drag & drop, multi-file, 500MB limit, all common formats |
| **File Management** | Upload, download, delete, preview (PDF/images), version replace |
| **Instant Sharing** | Send files directly to colleagues by username/email |
| **Shared Pages** | "Shared With Me" & "Shared By Me" with revoke access |
| **Folders** | Create folders, nested folders, department folders, move files |
| **Department Folders** | HR, Finance, Projects, Engineering, Management |
| **Global Search** | Search by filename, employee, department, date, file type |
| **Dashboard** | Recent files, storage usage, shared today, announcements |
| **Notifications** | Real-time bell, file share alerts, department uploads, announcements |
| **Admin Panel** | User management, access logs, broadcast messages, stats |
| **Dark/Light Mode** | Per-user theme preference |
| **Arabic Support** | RTL layout, Arabic name field, language toggle |
| **Responsive** | Works on desktop, tablet, and mobile |
| **Security** | CSRF protection, access control, IP logging, session management |

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# 1. Clone / unzip the project
cd kumoul-shared

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database (creates tables + sample accounts)
python init_db.py

# 5. Run the app
python run.py
```

Open your browser: **http://localhost:5000**

---

## 🔑 Default Accounts

### Admin
| Field | Value |
|---|---|
| Username | `admin` |
| Password | `Admin@123` |

### Sample Employees (all use password `Employee@123`)
| Username | Name | Department |
|---|---|---|
| ahmed.rashidi | Ahmed Al-Rashidi | Engineering |
| fatima.malik | Fatima Al-Malik | HR |
| omar.hassan | Omar Hassan | Finance |
| sara.ali | Sara Al-Ali | Projects |
| khalid.noor | Khalid Noor | Management |

> **⚠️ Change all passwords immediately after first login in production!**

---

## 🐳 Docker Deployment

```bash
# 1. Set environment variables (optional)
cp .env.example .env
# Edit .env with your values

# 2. Build and start
docker-compose up -d --build

# 3. View logs
docker-compose logs -f web
```

The app will be available at **http://your-server-ip**

---

## 🖥️ Production Deployment (Ubuntu Server)

### 1. Install prerequisites
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nginx postgresql
```

### 2. PostgreSQL Setup
```sql
sudo -u postgres psql
CREATE DATABASE kumoul_db;
CREATE USER kumoul_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE kumoul_db TO kumoul_user;
\q
```

### 3. Application Setup
```bash
cd /opt
sudo git clone <repo> kumoul-shared
cd kumoul-shared
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env
nano .env
# Set: DATABASE_URL=postgresql://kumoul_user:password@localhost/kumoul_db
# Set: SECRET_KEY=<strong-random-key>

python init_db.py
```

### 4. Systemd Service
```bash
sudo nano /etc/systemd/system/kumoul.service
```

```ini
[Unit]
Description=Kumoul SHARED
After=network.target postgresql.service

[Service]
User=www-data
WorkingDirectory=/opt/kumoul-shared
ExecStart=/opt/kumoul-shared/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app
Restart=always
EnvironmentFile=/opt/kumoul-shared/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable kumoul
sudo systemctl start kumoul
```

### 5. Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    location /static/ {
        alias /opt/kumoul-shared/app/static/;
        expires 30d;
    }
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 📁 Project Structure

```
kumoul-shared/
├── app/
│   ├── __init__.py          # App factory, extensions
│   ├── models.py            # Database models
│   ├── routes/
│   │   ├── auth.py          # Login, logout, profile
│   │   ├── dashboard.py     # Main dashboard
│   │   ├── files.py         # Upload, download, delete, preview
│   │   ├── folders.py       # Folder management
│   │   ├── sharing.py       # File sharing, user search API
│   │   ├── admin.py         # Admin panel, user management
│   │   └── search.py        # Search + notifications
│   ├── templates/
│   │   ├── base.html        # Master layout (sidebar, topbar)
│   │   ├── auth/            # Login, profile
│   │   ├── dashboard/       # Home, notifications
│   │   ├── files/           # List, upload, view, search
│   │   ├── shared/          # Shared with/by me
│   │   └── admin/           # Admin dashboard, create user
│   ├── static/
│   │   ├── css/main.css     # Full design system
│   │   └── js/main.js       # All interactions
│   └── uploads/             # File storage directory
├── docker/
│   └── nginx.conf
├── Dockerfile
├── docker-compose.yml
├── init_db.py               # DB initialization + sample data
├── run.py                   # App entry point
├── requirements.txt
└── .env.example
```

---

## 🔒 Security Notes

- All passwords are bcrypt-hashed
- CSRF tokens on all forms
- Per-file access control (own, shared, dept, company-wide)
- All actions logged with IP address and timestamp
- Session expires after 8 hours of inactivity
- Admin-only routes protected by decorator

---

## 🎨 Branding

- **Company**: Kumoul Engineering Consulting
- **Platform**: Kumoul SHARED
- **Primary Color**: Navy Blue `#1a3a6b`
- **Accent Color**: Orange `#e85d04`
- **Fonts**: Plus Jakarta Sans (EN), IBM Plex Sans Arabic (AR)

---

## 📞 Support

For technical issues, contact your IT administrator.

© Kumoul Engineering Consulting — Internal Use Only
