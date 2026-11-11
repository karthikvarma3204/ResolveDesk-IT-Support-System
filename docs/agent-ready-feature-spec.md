# Feature specification — Secure ticket access

An example of how to describe a feature to an AI coding assistant before implementation. This document **describes and reviews features already implemented** in ResolveDesk; it is not a historical record of an original prompt.

## Goal
Let teams manage support tickets while restricting privileged actions to the appropriate roles.

## User stories
- As an administrator, I can create a user with a permitted role so that access is controlled.
- As a support agent, I can create and resolve tickets but cannot administer identities.
- As a viewer, I can inspect requests and dashboard summaries without modifying data.
- As an unauthenticated visitor, I must sign in before opening protected pages.

## Acceptance criteria
1. Passwords are hashed; the database never stores plaintext passwords.
2. Login accepts valid credentials and rejects invalid ones with a generic message.
3. Protected routes redirect unauthenticated users to login.
4. Only admins can access `/admin/users` or create additional users.
5. Agents and admins can create and update tickets. Viewers receive HTTP 403 for unauthorized writes.
6. Closing or resolving a ticket requires a non-empty resolution note.
7. Forms that change state reject missing or mismatched CSRF tokens.
8. Logging out clears the session and prevents subsequent access to protected routes.
9. `/api/stats` requires login and returns counts by status and category.

## Test matrix
- Login: valid credentials, invalid credentials, password-hash verification.
- Access: anonymous redirect, agent permissions, viewer read-only, admin-only user provisioning.
- Input: invalid roles, missing CSRF, missing resolution note.
- Regression: ticket creation, dashboard aggregation and filtering.

## Security and operational notes
This is a local learning project. Add rate limiting, MFA, stronger audit logging, migrations, and production configuration before any enterprise deployment. Passing unit/route tests does not equal a security audit.

## Example pull-request checklist
- [ ] Scope and acceptance criteria documented
- [ ] Authentication and authorization paths reviewed
- [ ] Tests added or updated
- [ ] CI results checked
- [ ] README updated
- [ ] Remaining limitations documented
