# ResolveDesk — IT Support Ticket Management & Analytics

A responsive, AI-assisted **learning portfolio project** for managing IT service requests. Built with Python, Flask, SQLAlchemy, HTML, CSS and SQLite (MySQL optional).

> **Demo only — not production-ready.** This project does not implement authentication, role-based access controls, CSRF protection, or an audit log. Never enter confidential customer or company information.

## Features
- Dashboard showing total tickets, open/in-progress/resolved counts, priority and category breakdowns
- Create requests with category, priority, requester, title and description
- Search by ticket title and filter by status or priority
- Update ownership, status, priority and resolution notes
- Require resolution notes before marking tickets resolved or closed
- JSON stats endpoint at `/api/stats`
- Five optional sample tickets for a demonstration
- Responsive interface and automated HTTP workflow tests

## Technologies
Python 3.10+, Flask, Flask-SQLAlchemy, SQLAlchemy, SQLite, Jinja2, HTML and CSS. Optional MySQL through PyMySQL. Pytest and GitHub Actions for automated tests.

## Run on Windows (PowerShell)
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
flask --app app seed
flask --app app run --debug
```
Open **http://127.0.0.1:5000**.

## Run on macOS or Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
flask --app app seed
flask --app app run --debug
```

## Run tests
```bash
python -m pytest -q
```
CI also runs the tests using Python 3.10 and 3.12 on every push and pull request.

## Optional MySQL
Create a database:
```sql
CREATE DATABASE supportdesk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Edit `.env` and set:
```env
DATABASE_URL=mysql+pymysql://USERNAME:PASSWORD@localhost:3306/supportdesk
```
URL-encode special characters in your database password. SQLite works automatically if the `.env.example` defaults are kept.

## How it works
A user submits a form. Flask checks required fields and allowed categories/priorities, then SQLAlchemy saves the record to the database. The ticket list queries and filters the database. The dashboard groups tickets by status, category and priority. Support staff can assign, update, and resolve tickets; resolutions require written notes. The stats endpoint returns JSON summary data.

## Files
- `app.py` — Flask routes, ticket model, validation, sample-data command
- `templates/` — Jinja HTML pages
- `static/style.css` — dashboard and responsive interface
- `tests/test_app.py` — basic workflow checks
- `.github/workflows/tests.yml` — continuous integration test matrix
- `.env.example` — local configuration template (never commit your real `.env`)

## Demo walkthrough
1. Seed sample tickets and open the dashboard.
2. Create a high-priority request.
3. Filter tickets by priority and search.
4. Assign it and change the status to In Progress.
5. Add resolution notes and mark it Resolved.
6. Check the dashboard and `/api/stats`.

## Current limitations and improvements
This is a training project, not a deployed ITSM product. Before production use it would need authentication, RBAC, CSRF protection, database migrations, audit history, monitoring, pagination and deployment hardening.

**Project integrity:** Code and configuration were prepared using AI assistance. Do not claim independent implementation or runtime validation unless you have personally reviewed and tested it. The included GitHub Actions workflow reports automated test results on the repository's Actions tab.
