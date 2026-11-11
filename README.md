# ResolveDesk — IT Support & Access Management

An AI-assisted Python/Flask learning portfolio project combining help-desk workflows, login, password hashing and **role-based access control (RBAC)**.

> **Educational project, not enterprise IAM software.** No penetration test or external security audit has been performed.

## Features
- Username/password login with hashed passwords (Werkzeug)
- Server-side role-based permissions and least-privilege access controls
- **Administrator:** View tickets, create and resolve tickets, provision users and assign roles
- **Support Agent:** View, create and resolve tickets; no user-administration access
- **Viewer:** Read-only tickets and dashboard; cannot change any records
- CSRF tokens for state-changing forms; HttpOnly, SameSite session cookies; optional Secure cookies for HTTPS
- SQLAlchemy ticket management, filtering, ticket analytics and a protected JSON stats API
- Basic response security headers and automated access-control tests

## Role / permission table

| Feature | Admin | Agent | Viewer | Anonymous |
| --- | --- | --- | --- | --- |
| View tickets and analytics | Yes | Yes | Yes | No |
| Create/update tickets | Yes | Yes | No | No |
| Provision users and roles | Yes | No | No | No |

## Local setup

Requires Python 3.10+.

```bash
python -m venv .venv
# On Windows PowerShell: .venv\Scripts\Activate.ps1
# On macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
# Copy .env.example to .env and change SECRET_KEY to a strong value
flask --app app create-admin
flask --app app seed
flask --app app run
```

Visit http://127.0.0.1:5000/login. The `create-admin` command prompts for a username and password; passwords must be at least 12 characters. Create additional users in **Manage users**. No default credentials are committed.

## Tests

```bash
python -m pytest -q
```

GitHub Actions tests Python 3.10 and 3.12 on commits.

## Stack
Python, Flask, Flask-SQLAlchemy, Werkzeug, SQLite (optional MySQL using PyMySQL), Jinja2, HTML/CSS, pytest, GitHub Actions.

## Security limitations
This is a learning demonstration, **not a production-ready or formally compliant IAM platform**. It does not include MFA, SSO, login rate-limiting, password reset, audit history, account lockout, database migrations or external security testing. Use HTTPS and a strong SECRET_KEY for any nonlocal demo. The roles are enforced by Flask routes; this is not enterprise identity federation.

**Portfolio note:** Created with AI assistance; review the code and explain the authentication and authorization flow accurately during interviews.
