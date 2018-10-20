import os
import tempfile

import pytest
from gettor import create_app
from gettor import db as _db
from gettor.models.models import User, Show
from datetime import datetime


test_entries = [
    User('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f',
         False, 'test@test'),
    User('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79',
         True, 'other@other'),
    Show(name='test name', additional_search='more text', author_id=1,
         season=2, episode=4)
]

db_fd, TESTDB_PATH = tempfile.mkstemp()
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH


@pytest.fixture(scope='session')
def app(request):
    """Session-wide test `Flask` application."""
    global db_fd, TESTDB_PATH
    db_fd, TESTDB_PATH = tempfile.mkstemp()
    TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH
    settings_override = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
        'WTF_CSRF_ENABLED' : False
    }
    app = create_app(settings_override)

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope='session')
def db(app, request):
    """Session-wide test database."""
    if os.path.exists(TESTDB_PATH):
        os.close(db_fd)
        os.unlink(TESTDB_PATH)

    def teardown():
        _db.drop_all()
        try:
            os.close(db_fd)
        except OSError as e:
            pass
        os.unlink(TESTDB_PATH)

    _db.app = app
    _db.create_all()
    for entry in test_entries:
        _db.session.add(entry)
    _db.session.commit()

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope='function', autouse=True)
def session(app, db, request):
    """Creates a new database session for a test."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        options = dict(bind=connection, binds={})
        session = _db.create_scoped_session(options=options)

        session.begin_nested()
        _db.session = session

        def teardown():
            print("teardown1")
            transaction.rollback()
            connection.close()
            session.remove()

        request.addfinalizer(teardown)
        return session


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test', remember_me=False):
        return self._client.post(
            '/auth/login',
            data=dict(
                username=username,
                password=password,
                remember_me=remember_me
            ),
            follow_redirects=True
        )

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)