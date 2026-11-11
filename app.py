import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()
STATUSES = ('Open', 'In Progress', 'Resolved', 'Closed')
PRIORITIES = ('Low', 'Medium', 'High', 'Critical')
CATEGORIES = ('Software', 'Hardware', 'Network', 'Access', 'Other')

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
    )
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.route('/')
    def dashboard():
        total = db.session.query(func.count(Ticket.id)).scalar()
        counts = dict(db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all())
        categories = dict(db.session.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all())
        priorities = dict(db.session.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all())
        latest = Ticket.query.order_by(Ticket.created_at.desc()).limit(6).all()
        return render_template('dashboard.html', total=total, counts=counts, categories=categories, priorities=priorities, latest=latest)

    @app.route('/tickets')
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
    def new_ticket():
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            requester = request.form.get('requester', '').strip()
            category = request.form.get('category', 'Other')
            priority = request.form.get('priority', 'Medium')
            if not all([title, description, requester]) or len(title) > 120 or len(requester) > 100 or category not in CATEGORIES or priority not in PRIORITIES:
                flash('Please enter valid ticket details.', 'error')
            else:
                db.session.add(Ticket(title=title, description=description, requester=requester, category=category, priority=priority))
                db.session.commit()
                flash('Ticket created successfully.', 'success')
                return redirect(url_for('tickets'))
        return render_template('ticket_form.html', categories=CATEGORIES, priorities=PRIORITIES)

    @app.route('/tickets/<int:ticket_id>', methods=['GET', 'POST'])
    def ticket_detail(ticket_id):
        ticket = db.get_or_404(Ticket, ticket_id)
        if request.method == 'POST':
            status = request.form.get('status', '')
            priority = request.form.get('priority', '')
            assignee = request.form.get('assignee', '').strip()
            resolution = request.form.get('resolution', '').strip()
            if status not in STATUSES or priority not in PRIORITIES or len(assignee) > 100:
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
