import os
import secrets
import hmac
import click
from functools import wraps
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()
STATUSES = ('Open', 'In Progress', 'Resolved', 'Closed')
PRIORITIES = ('Low', 'Medium', 'High', 'Critical')
CATEGORIES = ('Software', 'Hardware', 'Network', 'Access', 'Other')


ROLES = ('admin', 'agent', 'viewer')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(15), nullable=False, default='viewer')
    active = db.Column(db.Boolean, nullable=False, default=True)

    def set_password(self, password):
        if len(password) < 12:
            raise ValueError('Password must be at least 12 characters.')
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def login_required(route):
    @wraps(route)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return route(*args, **kwargs)
    return wrapped

def roles_required(*allowed):
    def decorate(route):
        @wraps(route)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user.role not in allowed:
                abort(403)
            return route(*args, **kwargs)
        return wrapped
    return decorate

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requester = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(30), nullable=False, default='Other')
    priority = db.Column(db.String(20), nullable=False, default='Medium')
    status = db.Column(db.String(20), nullable=False, default='Open')
    assignee = db.Column(db.String(100), nullable=False, default='Unassigned')
    resolution = db.Column(db.Text, nullable=False, default='')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'development-only-change-me'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///supportdesk.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','false').lower() == 'true',
    )
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    with app.app_context():
        db.create_all()


    @app.before_request
    def check_security():
        uid = session.get('user_id')
        g.user = db.session.get(User, uid) if isinstance(uid, int) else None
        if g.user is not None and not g.user.active:
            session.clear()
            g.user = None
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            actual = request.form.get('csrf_token', '') or request.headers.get('X-CSRF-Token', '')
            expected = session.get('csrf_token', '')
            if not expected or not hmac.compare_digest(actual, expected):
                abort(400, description='Invalid CSRF token')

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'"
        return response

    def csrf_token():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        return session['csrf_token']

    @app.context_processor
    def globals_for_templates():
        return {'csrf_token': csrf_token, 'current_user': g.get('user')}

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '').strip().lower()
            user = User.query.filter_by(username=username).first()
            if user is not None and user.active and user.check_password(request.form.get('password', '')):
                session.clear()
                session['user_id'] = user.id
                session['csrf_token'] = secrets.token_urlsafe(32)
                session.permanent = True
                return redirect(url_for('dashboard'))
            flash('Invalid username or password.', 'error')
        return render_template('login.html')

    @app.post('/logout')
    @login_required
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/admin/users', methods=['GET', 'POST'])
    @roles_required('admin')
    def users():
        if request.method == 'POST':
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '')
            role = request.form.get('role', '')
            if not username or len(username) > 80 or len(password) < 12 or role not in ROLES or User.query.filter_by(username=username).first():
                flash('Invalid or duplicate user, role, or password.', 'error')
            else:
                user = User(username=username, role=role)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash('User created.', 'success')
                return redirect(url_for('users'))
        return render_template('users.html', users=User.query.order_by(User.id).all(), roles=ROLES)

    @app.cli.command('create-admin')
    @click.option('--username', prompt=True)
    @click.password_option(confirmation_prompt=True)
    def create_admin(username, password):
        username = username.strip().lower()
        if not username or len(username) > 80 or User.query.filter_by(username=username).first():
            raise click.ClickException('Invalid or duplicate username.')
        user = User(username=username, role='admin')
        try:
            user.set_password(password)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        db.session.add(user)
        db.session.commit()
        click.echo('Administrator created.')

    @app.route('/')
    @login_required
    def dashboard():
        total = db.session.query(func.count(Ticket.id)).scalar()
        counts = dict(db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all())
        categories = dict(db.session.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all())
        priorities = dict(db.session.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all())
        latest = Ticket.query.order_by(Ticket.created_at.desc()).limit(6).all()
        return render_template('dashboard.html', total=total, counts=counts, categories=categories, priorities=priorities, latest=latest)

    @app.route('/tickets')
    @login_required
    def tickets():
        q = Ticket.query
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        search = request.args.get('q', '').strip()
        if status in STATUSES:
            q = q.filter_by(status=status)
        if priority in PRIORITIES:
            q = q.filter_by(priority=priority)
        if search:
            q = q.filter(Ticket.title.ilike(f'%{search}%'))
        return render_template('tickets.html', tickets=q.order_by(Ticket.created_at.desc()).all(), statuses=STATUSES, priorities=PRIORITIES)

    @app.route('/tickets/new', methods=['GET', 'POST'])
    @roles_required('admin', 'agent')
    def new_ticket():
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            requester = request.form.get('requester', '').strip()
            category = request.form.get('category', 'Other')
            priority = request.form.get('priority', 'Medium')
            if not all([title, description, requester]) or len(title) > 120 or len(requester) > 100 or len(description) > 10000 or category not in CATEGORIES or priority not in PRIORITIES:
                flash('Please enter valid ticket details.', 'error')
            else:
                db.session.add(Ticket(title=title, description=description, requester=requester, category=category, priority=priority))
                db.session.commit()
                flash('Ticket created successfully.', 'success')
                return redirect(url_for('tickets'))
        return render_template('ticket_form.html', categories=CATEGORIES, priorities=PRIORITIES)

    @app.route('/tickets/<int:ticket_id>', methods=['GET', 'POST'])
    @login_required
    def ticket_detail(ticket_id):
        ticket = db.get_or_404(Ticket, ticket_id)
        if request.method == 'POST':
            if g.user.role not in ('admin', 'agent'):
                abort(403)
            status = request.form.get('status', '')
            priority = request.form.get('priority', '')
            assignee = request.form.get('assignee', '').strip()
            resolution = request.form.get('resolution', '').strip()
            if status not in STATUSES or priority not in PRIORITIES or len(assignee) > 100 or len(resolution) > 10000:
                flash('Invalid update.', 'error')
            elif status in ('Resolved', 'Closed') and not resolution:
                flash('A resolution is required before resolving or closing.', 'error')
            else:
                ticket.status, ticket.priority = status, priority
                ticket.assignee = assignee or 'Unassigned'
                ticket.resolution = resolution
                ticket.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                db.session.commit()
                flash('Ticket updated.', 'success')
                return redirect(url_for('ticket_detail', ticket_id=ticket.id))
        return render_template('ticket_detail.html', ticket=ticket, statuses=STATUSES, priorities=PRIORITIES)

    @app.route('/api/stats')
    @login_required
    def stats():
        return jsonify(
            total=Ticket.query.count(),
            by_status=dict(db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()),
            by_category=dict(db.session.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all()),
        )

    @app.cli.command('seed')
    def seed():
        if Ticket.query.count():
            print('Database already contains tickets; skipping seed.')
            return
        samples = [
            ('VPN connection fails', 'Remote VPN returns a connection timeout.', 'Asha', 'Network', 'High', 'In Progress', 'IT Support', ''),
            ('Password reset request', 'Account locked after repeated sign-in attempts.', 'Ravi', 'Access', 'Medium', 'Resolved', 'Help Desk', 'Identity verified and password reset.'),
            ('Laptop performance issue', 'Device is slow after startup.', 'Neha', 'Hardware', 'Low', 'Open', 'Unassigned', ''),
            ('Application login error', 'Portal shows an authentication error.', 'Arjun', 'Software', 'Critical', 'Open', 'Unassigned', ''),
            ('Printer unavailable', 'Office printer not detected on network.', 'Meera', 'Hardware', 'Medium', 'Closed', 'IT Support', 'Reinstalled printer driver and verified connectivity.'),
        ]
        for title, description, requester, category, priority, status, assignee, resolution in samples:
            db.session.add(Ticket(title=title, description=description, requester=requester, category=category, priority=priority, status=status, assignee=assignee, resolution=resolution))
        db.session.commit()
        print('Inserted five demo tickets.')
    return app

app = create_app()
if __name__ == '__main__':
    app.run(debug=True)
