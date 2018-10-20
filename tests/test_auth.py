import pytest
from flask import g, session
from gettor.models.models import User


def test_register(client, app, db):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'username': 'a', 'password': 'a', 'email': 'a'}
    )
    assert 'http://localhost/auth/login' == response.headers['Location']

    with app.app_context():
        user = db.session.query(User).filter_by(username='a').first()
        assert user is not None
        assert user.is_trainer is False

    assert client.get('/auth/register_trainer').status_code == 200
    response = client.post(
        '/auth/register_trainer', data={'username': 'b', 'password': 'b', 'email': 'b'}
    )
    assert 'http://localhost/auth/login' == response.headers['Location']

    with app.app_context():
        user2 = db.session.query(User).filter_by(username='b').first()
        assert user2 is not None
        assert user2.is_trainer is True


@pytest.mark.parametrize(('username', 'password', 'email', 'message'), (
        ('', '', '', [b'Username is required.', b'Password is required.', b'Email is required.']),
        ('a', '', '', [b'Password is required.', b'Email is required.']),
        ('a', 'a', '', b'Email is required.'),
        ('', 'a', '', [b'Username is required.', b'Email is required.']),
        ('test', 'test','test@test', b'already registered'),
))
def test_register_validate_input(client, username, password, email, message):
    response = client.post(
        '/auth/register',
        data={'username': username, 'password': password, 'email': email}
    )
    for m in message:
        assert m in response.data


def test_login(client, auth):
    assert client.get('/auth/login').status_code == 200
    response = auth.login()

    # path = [item[1] for item in response.headers if 'Set-Cookie' in item][0]
    path = response.headers['Set-Cookie']
    assert 'Path=/' in path

    with client:
        client.get('/')
        assert session['user_id'] == 1
        assert g.user.username == 'test'


@pytest.mark.parametrize(('username', 'password', 'message'), (
        ('a', 'test', b'Incorrect username.'),
        ('test', 'a', b'Incorrect password.'),
        ('', 'a', b'Username is required.'),
        ('test', '', b'Password is required.'),
))
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session
