# Security & Hardening Runbook

This document details the security posture, key rotation procedures, and pre-launch penetration testing checklists for the College Hostel Room Allocation System.

---

## 1. Key Rotation Procedures

### A. Django SECRET_KEY Rotation
* **Impact**: Invalidates existing active sessions (users will be prompted to re-authenticate) and revokes pending password reset tokens.
* **Frequency**: Rotate every 90 days or immediately upon suspected breach.
* **Procedure**:
  1. Generate a new secret key:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(50))"
     ```
  2. Update the `SECRET_KEY` environment variable on your hosting dashboard (AWS ECS / Heroku / Railway / Kubernetes Secrets).
  3. Perform a zero-downtime rolling restart of the web service.

### B. Database Password Rotation
* **Procedure**:
  1. In PostgreSQL, create or update user credentials:
     ```sql
     ALTER USER hostel_user WITH PASSWORD 'new_super_secure_password';
     ```
  2. Update `DATABASE_URL` in the production environment variables.
  3. Restart the container/application instances.

### C. Email SMTP Credential Rotation
* **Procedure**:
  1. Generate a new App Password in your mail provider (e.g., Google Workspace / SendGrid / AWS SES).
  2. Update `EMAIL_HOST_PASSWORD` in the environment variables.
  3. Trigger a test notification or password reset email to verify delivery.

---

## 2. Security Controls Implemented

| Category | Control | Verification |
|---|---|---|
| **SQL Injection** | Django ORM with parameterization throughout; zero raw concatenated SQL | Automated static analysis & ORM inspection |
| **XSS** | Template auto-escaping enabled; strict Content-Security-Policy header | `SecurityHeadersMiddleware` |
| **CSRF** | `CsrfViewMiddleware` with SameSite=Lax cookie and token verification | Form auditing & test suite |
| **Clickjacking** | `X_FRAME_OPTIONS = 'DENY'` + CSP `frame-ancestors 'none'` | Response header inspection |
| **Open Redirects** | `url_has_allowed_host_and_scheme()` validation on all `?next=` parameters | Accounts views test suite |
| **Brute-Force & Credential Stuffing** | Account lockout after 5 consecutive failed attempts (15 min cooldown) + IP rate limiting (15 req/min on auth) | `RateLimitMiddleware` & `accounts/views.py` |
| **File Uploads** | File extension allowlist (JPG, PNG, WEBP), 5MB size limit, UUID renaming | `validate_maintenance_photo` & `maintenance_photo_upload_path` |
| **Session Security** | 30-min inactivity timeout, `HttpOnly`, `Secure` (in prod), `SameSite=Lax` | `hostel_project/settings.py` |
| **RBAC / IDOR** | Server-side role decorators (`@admin_required`, `@warden_required`, `@student_required`, `@accountant_required`) | Automated test coverage |
| **Concurrency / Double Booking** | `transaction.atomic()` with `select_for_update()` on room occupancy | `allocations/services.py` |

---

## 3. Pre-Launch Penetration Testing Checklist

Run these manual or automated checks (e.g. using OWASP ZAP or Postman) before public launch:

- [ ] **Open Redirect Test**:
  - Request `GET /accounts/login/?next=https://attacker.com`
  - Submit valid login credentials.
  - Verify browser is redirected to `/accounts/dashboard-redirect/` and NOT `attacker.com`.
- [ ] **Brute-Force Lockout Test**:
  - Send 5 consecutive incorrect passwords for an account.
  - Verify the 5th attempt locks the account with a 15-minute cooldown message.
- [ ] **IDOR Protection Test**:
  - Sign in as `student_boy`.
  - Attempt to view or rate another student's maintenance ticket or fee receipt by directly altering the ID in the URL.
  - Verify access is rejected (403 or redirect).
- [ ] **Rate Limiting Test**:
  - Send 20 rapid GET requests to `/accounts/login/` within 30 seconds.
  - Verify HTTP 429 Too Many Requests response with `Retry-After` header.
- [ ] **Executable Upload Test**:
  - Attempt to upload `test.php` or `script.exe` as a maintenance photo.
  - Verify upload is rejected with a validation error.
- [ ] **Debug Leakage Test**:
  - Request an invalid URL `/does-not-exist/` when `DEBUG=False`.
  - Verify clean 404 page is rendered with zero stack trace or internal path disclosures.
- [ ] **Health Check Test**:
  - Request `GET /health/`.
  - Verify response is `{"status": "healthy", ...}` with HTTP 200.
