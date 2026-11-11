# Student Record System

A secure, role-based student information management system developed using Django and Django REST Framework. The application centralizes student records, academic administration, course enrollment, attendance, grading, fee management, and institutional reporting.

The system provides dedicated interfaces for students, faculty, administrators, and system administrators, supported by REST APIs, role-based access control, and secure data management.

---

## 1. Features

### Authentication and User Management
- Secure login using JWT authentication.
- Role-based access control (RBAC).
- Password reset with OTP verification.
- Account lockout after repeated failed login attempts.
- Security alerts and audit logging.

### Student Management
- Student registration and profile management.
- Unique student identification.
- Approval-based profile modifications.
- Secure document upload and retrieval.
- Student record validation.

### Academic Management
- Management of programs, semesters, courses, and prerequisites.
- Faculty assignments and course offerings.
- Course eligibility verification.
- Enrollment and withdrawal management.
- Seat availability and duplicate enrollment checks.

### Attendance Management
- Faculty-managed attendance sessions.
- Attendance recording and modification.
- Automatic attendance percentage calculation.
- Low-attendance identification and reporting.

### Grading and Transcripts
- Assessment and grade management.
- Grade finalization and controlled overrides.
- GPA and CGPA calculation.
- Transcript generation in PDF format.
- Transcript verification.

### Finance Management
- Student fee invoice generation.
- Scholarship adjustments.
- Payment processing through a mock payment gateway.
- Payment verification and receipt generation.
- Duplicate payment prevention.

### Reporting and Auditing
- Role-specific dashboards.
- Academic and administrative reports.
- PDF and Excel exports.
- Audit logging and security monitoring.

---

## 2. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | Django 5.2 |
| API Framework | Django REST Framework |
| Frontend | HTML, CSS, JavaScript, Django Templates |
| Database | MySQL 8 / SQLite |
| Authentication | JWT, Argon2 |
| Web Server | Gunicorn, Nginx |
| Containerization | Docker, Docker Compose |
| Testing | Django Test Framework, pytest, coverage.py |
| Version Control | Git, GitHub |
| Project Management | GitHub Issues, Projects, Pull Requests |
| CI/CD | GitHub Actions (configuration subject to verification) |

---

## 3. System Architecture

The application follows a **modular monolithic architecture**, separating the presentation layer, business logic, and data persistence layer.

```text
               Client Browser
                     |
                     v
             Django Templates
               HTML/CSS/JS
                     |
                     v
               Nginx Proxy
                     |
                     v
            Django Application
                     |
           +---------+---------+
           |                   |
           v                   v
      REST API           Web Interface
           |                   |
           +---------+---------+
                     |
                     v
             Business Logic
                     |
                     v
              Database Layer
              MySQL / SQLite
```

Nginx is used in the containerized deployment; local development uses Django's development server.

### Project Modules

| Module | Description |
|---|---|
| `accounts/` | Authentication, user accounts, and security |
| `students/` | Student registration and profile management |
| `academic/` | Academic programs, courses, and semesters |
| `enrollments/` | Course enrollment and withdrawal |
| `attendance/` | Attendance tracking and reporting |
| `grading/` | Grades, GPA, CGPA, and transcripts |
| `finance/` | Fees, invoices, and payments |
| `portal/` | Role-based interfaces and dashboards |
| `core/` | Shared security, encryption, auditing, and utilities |
| `config/` | Django configuration |
| `tests/` | Automated test cases |
| `docs/` | Technical documentation |

---

## 4. Installation and Setup

### Prerequisites

Ensure the following are installed:

- Python 3.11 or newer
- pip
- Git
- OpenSSL
- Docker and Docker Compose (optional)

### Clone the Repository

```bash
git clone https://github.com/ananya97br/student-record-system.git

cd student-record-system
```

### Create a Virtual Environment

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

```bash
cp .env.example .env
```

Generate the local development configuration:

```bash
python3 scripts/bootstrap.py
```

### Apply Database Migrations

```bash
python manage.py migrate
```

### Run the Application

```bash
python manage.py runserver
```

Open the application at:

**http://127.0.0.1:8000/login**

The local development environment uses SQLite by default.

---

## 5. Docker Setup

The Docker deployment uses:

- MySQL for database management.
- Django for application services.
- Gunicorn as the application server.
- Nginx as the reverse proxy.
- Mailpit for development email testing.

Configure the environment:

```bash
cp .env.example .env

python3 scripts/bootstrap.py
```

Start the containers:

```bash
docker compose up --build
```

Access the application at:

**http://localhost:8000**

Access the Mailpit interface at:

**http://localhost:8025**

---

## 6. User Roles

The system supports four principal roles.

| Role | Responsibilities |
|---|---|
| Student | View and update permitted profile information, enroll in courses, view attendance, grades, transcripts, and fees |
| Faculty | Manage assigned course attendance, enter grades, and access relevant academic information |
| Administrator | Manage student records, academic configurations, enrollment, reports, and administrative workflows |
| System Administrator | Manage user access, system-level configuration, and security monitoring |

Permissions are enforced through server-side role and ownership checks.

---

## 7. API Endpoints

The application provides REST APIs for authentication, student management, academic administration, enrollment, attendance, grading, finance, and reports.

| Endpoint | Description |
|---|---|
| `/login` | Login interface |
| `/portal/dashboard` | User dashboard |
| `/admin/` | Django administration |
| `/api/docs` | API documentation |
| `/api/openapi.json` | OpenAPI specification |
| `/health/live` | Application liveness |
| `/health/ready` | Application readiness |

For detailed endpoint information, refer to `docs/API.md`.

---

## 8. Testing

The project includes automated tests covering important functional and security requirements.

### Run System Checks

```bash
python manage.py check
```

### Run Unit and Integration Tests

```bash
python manage.py test tests -v 2
```

### Generate Code Coverage

```bash
coverage run --branch manage.py test tests

coverage report -m

coverage html
```

This produces a terminal coverage summary and an HTML report.

### Testing Scope

Testing covers authentication, authorization, student registration, enrollment constraints, attendance, grading, payment handling, reporting, encryption, and auditing.

Additional testing documentation is available in `docs/TEST_MATRIX.md`.

---

## 9. GitHub Project Management

The project uses GitHub for version control, requirement tracking, collaboration, and development management.

The GitHub backlog includes:

- Functional Requirements (FR)
- Non-Functional Requirements (NFR)
- Security Requirements
- Development and Testing Activities

Each backlog item can be associated with story points, sprint allocation, responsible team members, and implementation evidence.

Development activities are organized using GitHub Issues, feature branches, pull requests, and code reviews.

Historical commits are linked to relevant issues for retrospective requirement traceability.

---

## 10. CI/CD Pipeline

The planned CI/CD workflow uses **GitHub Actions** for automated application validation and Docker image delivery.

The pipeline is designed to perform the following activities:

1. Check out the latest repository code.
2. Set up Python and install dependencies.
3. Execute Django system checks.
4. Run automated tests.
5. Generate code and branch coverage reports.
6. Upload test reports as GitHub Actions artifacts.
7. Build a Docker image after successful validation.
8. Publish the image to GitHub Container Registry.

The workflow is intended to run on pull requests and updates to the `main` branch.

**Status:** Confirm that `.github/workflows/ci-cd.yml` exists and has a successful execution before treating the pipeline as operational. The uploaded repository snapshot did not contain a GitHub Actions workflow.

Container publishing provides continuous delivery; automatic production deployment is not included.

---

## 11. Security

Security is incorporated into the application's authentication, authorization, storage, and administrative workflows.

Implemented security mechanisms include:

- JWT-based authentication.
- Argon2 password hashing.
- Role-based access control.
- CSRF protection.
- OTP-based password recovery.
- Account lockout and security alerts.
- Encryption of selected sensitive information.
- Audit logging.
- Document validation and access restrictions.
- Transactional and idempotent payment handling.

The bundled payment gateway and document scanner are development-oriented implementations.

Production deployment requires additional configuration, including trusted HTTPS certificates, secure credential management, monitoring, and backups.

Refer to `docs/SECURITY.md` for further details.

---

## 12. Documentation

The repository contains the following technical documentation:

| Document | Description |
|---|---|
| `docs/ARCHITECTURE.md` | System architecture and design |
| `docs/API.md` | API specifications |
| `docs/SECURITY.md` | Security mechanisms |
| `docs/OPERATIONS.md` | Operational and deployment procedures |
| `docs/TEST_MATRIX.md` | Requirements and test case traceability |
| `docs/DECISIONS.md` | Design decisions and deviations |

---