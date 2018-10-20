from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Register')


class DeleteForm(FlaskForm):
    delete = SubmitField('Delete')


class StartDownloadFromUpdateForm(FlaskForm):
    start = SubmitField('Start Download')


class ShowForm(FlaskForm):
    name = StringField('Show name', validators=[DataRequired("Please enter your name.")])
    additional_search = StringField('additional search words')
    season = IntegerField('Season to start with', validators=[DataRequired("Please enter season number.")])
    episode = IntegerField('Episode to start with', validators=[DataRequired("Please enter episode number.")])


class AddShowForm(ShowForm):
    submit = SubmitField('Add Show')


class UpdateShowForm(ShowForm):
    submit = SubmitField('Update Show')


class DownloadForm(FlaskForm):
    download = SubmitField('Download')


class NextEpForm(FlaskForm):
    download = SubmitField('Download this Episode')
    next = SubmitField('Search Next Episode')
    next_url = SubmitField('>')
    prev_url = SubmitField('<')

