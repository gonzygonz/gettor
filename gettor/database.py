import os
import click
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from flask import current_app, g

db = SQLAlchemy()


def get_db():
    if 'db' not in g:
        g.db = db
    return g.db


def close_db(e=None):
    db.session.remove()


def init_db():
    db.drop_all()
    from gettor.models.models import User, Show, ShowToTvmaze
    db.create_all()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


