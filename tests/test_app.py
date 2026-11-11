import pytest
from app import create_app, db, Ticket

@pytest.fixture
def client():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'SECRET_KEY': 'test'})
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_dashboard(client):
    assert client.get('/').status_code == 200
    assert b'Operations dashboard' in client.get('/').data

def test_create_and_filter_ticket(client):
    response = client.post('/tickets/new', data={'title':'Cannot login','description':'Error on sign in','requester':'Tester','category':'Access','priority':'High'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Cannot login' in response.data
    assert b'Cannot login' in client.get('/tickets?priority=High&q=login').data
    assert client.get('/api/stats').json['total'] == 1

def test_resolution_required(client):
    client.post('/tickets/new', data={'title':'VPN issue','description':'Connection failure','requester':'Tester','category':'Network','priority':'High'})
    response = client.post('/tickets/1', data={'status':'Resolved','priority':'High','assignee':'Support','resolution':''}, follow_redirects=True)
    assert b'resolution is required' in response.data
    response = client.post('/tickets/1', data={'status':'Resolved','priority':'High','assignee':'Support','resolution':'Reset configuration'}, follow_redirects=True)
    assert b'Ticket updated' in response.data

def test_rejects_invalid_ticket_fields(client):
    response = client.post('/tickets/new', data={'title': 'Issue', 'description': 'Description', 'requester': 'Tester', 'category': 'Unknown', 'priority': 'High'}, follow_redirects=True)
    assert b'valid ticket details' in response.data
    assert client.get('/api/stats').json['total'] == 0

def test_nonexistent_ticket_returns_404(client):
    assert client.get('/tickets/99999').status_code == 404

def test_status_update_and_dashboard_counts(client):
    client.post('/tickets/new', data={'title': 'Email outage', 'description': 'Cannot send mail', 'requester': 'Tester', 'category': 'Software', 'priority': 'Critical'})
    client.post('/tickets/1', data={'status': 'In Progress', 'priority': 'High', 'assignee': 'Help Desk', 'resolution': ''})
    assert client.get('/api/stats').json['by_status']['In Progress'] == 1
    assert b'Help Desk' in client.get('/tickets/1').data
