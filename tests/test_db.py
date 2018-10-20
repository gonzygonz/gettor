import sqlite3
import pytest
import sqlalchemy
from gettor.database import get_db



def test_get_close_db(app):
    with app.app_context():
        db_ = get_db()
        assert db_ is get_db()
