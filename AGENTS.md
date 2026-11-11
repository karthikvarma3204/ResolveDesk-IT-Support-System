# ResolveDesk — AI coding assistant guidance

This document is a reusable guide for AI coding agents and human contributors. The project began as AI-assisted portfolio work; do not assume this file was present for earlier commits.

## Purpose and scope
Maintain a learning-scale Flask IT support application with user login, role-based access and ticket analytics. Keep the application understandable for early-career developers.

## Architecture
- `app.py`: Flask factory, SQLAlchemy models, authentication, authorization, business rules and routes.
- `templates/`: server-rendered Jinja HTML views.
- `static/style.css`: responsive interface.
- `tests/test_app.py`: pytest functional and access-control checks.
- `.github/workflows/tests.yml`: automated Python tests.

## Agent workflow
1. Restate the requested feature and user-visible acceptance criteria before editing.
2. Identify affected routes, models, templates, and tests; prefer small changes.
3. Keep password secrets out of source control. Use Werkzeug password hashing; never store plaintext passwords.
4. Enforce authorisation **server-side**, not only by hiding buttons.
5. Include CSRF tokens on state-changing forms.
6. Keep SQLAlchemy database operations consistent; do not interpolate untrusted SQL.
7. Add tests for successful operations, invalid inputs and permission denial.
8. Run `python -m pytest -q`; never claim tests passed unless they actually ran.
9. Explain changes, risks, untested paths and limitations in the pull-request description.

## Permission requirements
- Administrator: view and manage tickets; provision users.
- Support Agent: view and manage tickets; cannot provision users.
- Viewer: view tickets and analytics only.
- Unauthenticated: redirected to login for protected pages and API.

## Definition of done
- Behaviour matches the feature's acceptance criteria.
- Tests cover the expected flow and at least one failure/permission path.
- UI is usable at narrow and desktop widths.
- Documentation is updated if setup or behavior changes.
- CI passes on Python 3.10 and 3.12.

## Do not claim
This educational repository does not provide enterprise IAM, MFA, SSO, Azure deployment, or production compliance certification.
