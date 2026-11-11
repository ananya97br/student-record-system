# Student Record System

A robust, secure **Student Record System** built with Python and Django, featuring comprehensive role-based access control, enrollment management, attendance tracking, grading engines, transcripts, fee management, and an integrated web portal.

## 📑 Table of Contents
- [Overview](#overview)
- [Key Features & Modules](#key-features--modules)
- [Security Controls](#security-controls)
- [Security Alerts & Monitoring](#security-alerts--monitoring)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)

---

## 🔍 Overview
The Student Record System is engineered to handle core academic operations securely and efficiently. It incorporates strict security boundaries, robust authorization checks, immutable audit logging, and transactional safety across enrollments, grading, and financial transactions.

---

## 🚀 Key Features & Modules

| Module | Description |
| :--- | :--- |
| **Accounts & RBAC** | Role-based access control with default-deny permissions, ownership checks, and secure session management. |
| **Enrollments & Attendance** | Manages course registrations, student attendance tracking, and faculty comments with transaction and row locks. |
| **Grading & Transcripts** | Automated GPA and CGPA calculation engines, grade finalization, and secure transcript generation. |
| **Finance & Fee Management** | Invoice generation, payment callbacks with idempotency safeguards, and receipt creation. |
| **Portal & Reports** | Web portal routes for students, faculty, and administrators with bulk export monitoring. |

---

## 🔒 Security Controls

* **Authentication & Passwords:** Passwords are secured using Django's `Argon2id` hasher. Plaintext passwords are never persisted or logged.
* **OTPs & Tokens:** One-Time Passwords (OTPs) are hashed with a server secret, expire after 10 minutes, and are invalidated upon new issuance or usage within a transaction. JWTs are signed and delivered via `HttpOnly`, `SameSite=Lax` cookies.
* **Data Encryption:** AES-256-GCM protects sensitive contact information, marks/results, and payment reference values. Payment reference HMACs enable callback lookup without plaintext database indexing.
* **Document Protection:** File uploads undergo extension allow-listing, declared MIME validation, magic signature checks, 5 MB size limits, randomized paths, checksum verification, deterministic malware scanning, and owner/admin download authorization.
* **Audit Immutability:** Audit logs reject ORM updates and deletes, supported by database triggers to ensure complete tamper resistance.

---

## 🚨 Security Alerts & Monitoring

The system actively records operational audit events and triggers security alerts:
* **Account Lockout:** Five consecutive failed login attempts trigger an account lock, record an `ACCOUNT_LOCK` audit event, issue a high-severity `REPEATED_LOGIN_FAILURE` alert, and send a notification.
* **Bulk Export Monitoring:** At least five report exports by the same actor within five minutes generate a high-severity `BULK_EXPORT` alert. Unresolved bulk export alerts are reused rather than duplicated.
* **Management API:** Administrators can review alerts via `GET /api/auth/security-alerts` and resolve them via `POST /api/auth/security-alerts/<id>/resolve`.

---

## 🛠️ Tech Stack
* **Backend:** Python, Django
* **Database & Infrastructure:** MySQL / SQLite fallback, Docker, Docker Compose
* **Testing & Quality:** pytest, k6 load testing scripts, CI/CD pipelines

---
