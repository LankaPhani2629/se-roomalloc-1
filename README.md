# College Hostel Room Allocation System

A full-stack, rule-based web application for college residential housing management built with Python Django, HTML/CSS/JavaScript with Bootstrap 5, and SQLite.

## Table of Contents
- [Overview](#overview)
- [Key Business Rules & Constraints](#key-business-rules--constraints)
- [Role-Based Access Control](#role-based-access-control)
- [System Architecture & Apps](#system-architecture--apps)
- [Installation & Setup](#installation--setup)
- [Running Migrations](#running-migrations)
- [Executing Unit & SRS Test Cases](#executing-unit--srs-test-cases)
- [Export Features](#export-features)
- [Security Review](#security-review)

---

## Overview
The Hostel Room Allocation System automates the complete student housing lifecycle on a college campus—from initial registration and preference-based application submission, warden verification, automated rule-based room allotment, fee confirmation, room transfers and vacating, through to complaints resolution and comprehensive analytics reports.

## Key Business Rules & Constraints
1. **Gender Restriction**: Boys and girls are allotted strictly to their respective hostels (`BOYS` vs `GIRLS`).
2. **Room Capacity Guard**: A room can never exceed its capacity. Enforced at the database level with a `CheckConstraint(occupied_count <= capacity)` and inside atomic transactions with `select_for_update()`.
3. **Single Active Allotment**: A student can possess only one active room allotment across campus.
4. **Fee Payment & Allotment Confirmation**: Room allotment is marked as `PENDING_PAYMENT` with a due date. It is marked as `CONFIRMED` only when paid by the due date; otherwise it is marked as `EXPIRED` and the bed is released back into inventory.
5. **Configurable Priority Rules**: Administrator defines priority weights (merit score, year of study, target room types) for the automated allocation algorithm.

---

## Role-Based Access Control
The application implements four distinct user roles, protected via custom role decorators (`@role_required`, `@admin_required`, `@warden_required`, `@student_required`, `@accountant_required`):

| Role | Responsibilities |
|---|---|
| **Student** | Register, manage profile, submit room application, view allotment & roommates, request room change or vacating, track fees & receipts, log complaints. |
| **Warden** | Verify student applications (approve/waitlist/reject), execute manual room allotments, review room change and vacating requests, update and resolve maintenance complaints. |
| **Administrator** | Manage hostels and room inventory, configure allocation priority rules, open/close application windows, run batch auto-allocation engine, review students and reports. |
| **Accountant** | Configure fee structures per room type, record payments with receipt numbers, track pending dues, batch-expire overdue allotments, view financial reports. |

---

## System Architecture & Apps
The project follows Django's modular app architecture:
- `accounts`: Custom `User` model with role choices, student registration, authentication, password changing, and role-based redirect.
- `hostels`: `Hostel` and `Room` models, capacity management, room search, filtering, and CRUD views.
- `applications`: `Student` profile, `ApplicationPeriod` window control, and `Application` verification workflow.
- `allocations`: `Allocation`, `RoomChangeRequest`, `AllocationRule`, and `services.py` containing the automatic priority allocation engine and atomic room transfer services.
- `fees`: `FeeStructure`, `FeePayment`, receipt generation (`RCP...`), pending dues monitoring, and allotment confirmation logic.
- `complaints`: `Complaint` logging across categories (civil, electrical, plumbing, cleanliness) with tracking and warden resolution.
- `notifications`: In-app notification bell icon with live unread counter, and automated email dispatches via Django's console email backend.
- `reports`: Dynamic dashboards for all 4 roles, and exportable reports (Occupancy, Vacancy, Allocation List, Fee Dues, Complaints) in PDF and Excel formats.

---

## Installation & Setup

### 1. Clone Repository & Setup Environment
```bash
git clone https://github.com/LankaPhani2629/se-roomalloc-1.git
cd se-roomalloc-1
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Administrator (Optional)
```bash
python manage.py createsuperuser
```

### 5. Launch Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## Executing Unit & SRS Test Cases
The system includes an automated test suite covering all SRS functional requirements:
- Valid and invalid login authentication
- Role redirection & password hashing
- Unauthorized access denied (403 Permission Denied)
- Application submission (open vs closed window)
- Warden application review and approval
- Allocation with free capacity
- Full room denial (capacity boundary)
- Wrong-gender hostel denial
- Single active allotment constraint
- Room change atomic transfer
- Room vacating workflow
- Fee payment confirmation & overdue expiry
- Occupancy report rendering & PDF/Excel export

Run the complete test suite:
```bash
python manage.py test
```

---

## Export Features
Reports can be exported in two formats:
- **PDF Export**: Built with `ReportLab` using styled tables, custom headers, page sizing, and colored status accents.
- **Excel (.xlsx) Export**: Built with `openpyxl` with column auto-fitting, styled headers, and cell formatting.

---

## Security Review
- **CSRF Protection**: All form submissions include `{% csrf_token %}` tokens.
- **Input Validation**: Django Forms validate fields, student registration prevents duplicates, and model validators enforce data integrity.
- **Role Enforcement**: Every view is wrapped with role-based checks (`@role_required`). Direct URL tampering is prevented.
- **Password Security**: Passwords are securely hashed with PBKDF2 with SHA-256 via Django's authentication framework.
- **Race Condition Prevention**: Database transactions (`transaction.atomic()`) and row locking (`select_for_update()`) protect against double-booking and concurrent capacity overages.
