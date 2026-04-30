# Kumoul Shared — File Management System

## Overview

Kumoul Shared is an internal file management platform developed for Kumoul Engineering Consulting.
It provides a centralized system for uploading, organizing, and securely sharing files between users and teams.

The system is designed to be simple, maintainable, and scalable using a lightweight web architecture.

---

## Key Features

* Upload and manage files
* Share files between users
* Folder organization (including nested folders)
* Search and filtering
* Role-based access control (admin / user)
* Responsive web interface

---

## Tech Stack

* **Backend:** Python (Flask)
* **Database:** PostgreSQL / SQLite
* **ORM & Migrations:** SQLAlchemy, Alembic
* **Storage:** AWS S3 (or local storage for development)
* **Frontend:** HTML, CSS, JavaScript (Jinja2 templates)
* **Deployment:** Docker, Nginx

---

## Project Structure

```bash
kumoul-shared/
│
├── app/                # Main application (routes, models, templates)
├── migrations/         # Database migrations (Alembic)
├── docker/             # Docker and deployment configs
├── run.py              # Application entry point
├── requirements.txt
└── .env.example
```

---

## Setup (Development)

```bash
git clone https://github.com/saljedani/kumoul-shared.git
cd kumoul-shared

python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt
python init_db.py
python run.py
```

Then open:
http://localhost:5000

---

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
DATABASE_URL=
SECRET_KEY=
AWS_ACCESS_KEY=
AWS_SECRET_KEY=
S3_BUCKET=
```

---

## Notes

* Sensitive credentials are not stored in the repository
* Environment variables are used for configuration
* The project structure follows a modular Flask design

---

## Disclaimer

This repository contains a development version of the system.
Production-specific configurations and sensitive data are not included.

---

© Kumoul Engineering Consulting
