import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask import render_template
from gettor.forms.forms import LoginForm, RegisterForm
from gettor import db
from gettor.models.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


def register_helper(username, password, email):
    error = None

    if not username:
        error = 'Username is required.'
    elif not password:
        error = 'Password is required.'
    elif not email:
        error = 'Email is required.'
    elif db.session.query(User).filter_by(username=username).first():
        error = 'User {} is already registered.'.format(username)
    return error


def register(is_trainer):
    form = RegisterForm()
    if form.validate_on_submit():

        error = register_helper(form.username.data, form.password.data, form.email.data)
        if error is None:
            new_user = User(username=form.username.data,
                            password=generate_password_hash(form.password.data),
                            is_trainer=is_trainer,
                            email=form.email.data)
            flash('registering user {} '.format(
                form.username.data))
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('auth.login'))

        flash(error)
    return render_template('auth/register.html', title='Register User', form=form)


@bp.route('/register', methods=('GET', 'POST'))
def register_user():
    return register(False)


@bp.route('/register_trainer', methods=('GET', 'POST'))
def register_trainer():
    return register(True)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            error = None
            user = db.session.query(User).filter_by(username=username).first()
            if user is None:
                error = 'Incorrect username.'
            elif not check_password_hash(user.password, password):
                error = 'Incorrect password.'

            if error is None:
                session.clear()
                session['user_id'] = user.id
                flash('Login requested for user {}, remember_me={}'.format(
                    form.username.data, form.remember_me.data))
                return redirect(url_for('index'))
            flash(error)
    return render_template('auth/login.html', title='Log In', form=form)


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = db.session.query(User).filter_by(id=user_id).first()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
