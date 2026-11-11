import pytest
from app import create_app, db, User

@pytest.fixture
def client():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'SECRET_KEY': 'test-secret'})
    with app.app_context():
        for username, role in [('admin','admin'),('agent','agent'),('viewer','viewer')]:
            user = User(username=username, role=role)
            user.set_password('strong-password-123')
            db.session.add(user)
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def token(client):
    with client.session_transaction() as sess:
        return sess['csrf_token']

def login(client, username='admin'):
    client.get('/login')
    return client.post('/login', data={'username':username,'password':'strong-password-123','csrf_token':token(client)}, follow_redirects=True)

def create_ticket(client):
    return client.post('/tickets/new', data={'title':'VPN unavailable','description':'Cannot connect remotely','requester':'Tester','category':'Network','priority':'High','csrf_token':token(client)}, follow_redirects=True)

def test_anonymous_requires_login(client):
    for path in ('/','/tickets','/tickets/new','/api/stats'):
        assert client.get(path).status_code == 302

def test_hashed_password_and_login(client):
    with client.application.app_context():
        u = User.query.filter_by(username='admin').first()
        assert u.password_hash != 'strong-password-123'
        assert u.check_password('strong-password-123')
        assert not u.check_password('wrong')
    assert b'Operations dashboard' in login(client).data

def test_bad_password(client):
    client.get('/login')
    response = client.post('/login', data={'username':'admin','password':'wrong','csrf_token':token(client)})
    assert b'Invalid username or password' in response.data
    assert client.get('/').status_code == 302

def test_missing_csrf_is_rejected(client):
    login(client)
    assert client.post('/tickets/new', data={'title':'x'}).status_code == 400

def test_agent_create_and_resolve(client):
    login(client, 'agent')
    assert b'VPN unavailable' in create_ticket(client).data
    response = client.post('/tickets/1', data={'status':'Resolved','priority':'High','assignee':'Support','resolution':'','csrf_token':token(client)}, follow_redirects=True)
    assert b'resolution is required' in response.data
    response = client.post('/tickets/1', data={'status':'Resolved','priority':'High','assignee':'Support','resolution':'Updated VPN config','csrf_token':token(client)}, follow_redirects=True)
    assert b'Ticket updated' in response.data
    assert client.get('/api/stats').json['by_status']['Resolved'] == 1

def test_viewer_read_only(client):
    login(client, 'admin')
    create_ticket(client)
    client.post('/logout', data={'csrf_token':token(client)})
    login(client, 'viewer')
    assert client.get('/tickets').status_code == 200
    assert client.get('/tickets/new').status_code == 403
    assert client.post('/tickets/1', data={'status':'Closed','priority':'Low','assignee':'x','resolution':'x','csrf_token':token(client)}).status_code == 403
    assert client.get('/admin/users').status_code == 403

def test_agent_cannot_create_users(client):
    login(client,'agent')
    assert client.get('/admin/users').status_code == 403

def test_admin_user_provisioning(client):
    login(client)
    result = client.post('/admin/users', data={'username':'new-viewer','password':'new-long-password-123','role':'viewer','csrf_token':token(client)}, follow_redirects=True)
    assert b'new-viewer' in result.data
    with client.application.app_context():
        assert User.query.filter_by(username='new-viewer').first().role == 'viewer'

def test_invalid_role_rejected(client):
    login(client)
    client.post('/admin/users', data={'username':'bad-user','password':'new-long-password-123','role':'root','csrf_token':token(client)})
    with client.application.app_context():
        assert User.query.filter_by(username='bad-user').first() is None

def test_logout_revokes_session(client):
    login(client)
    assert client.post('/logout',data={'csrf_token':token(client)}).status_code == 302
    assert client.get('/').status_code == 302
