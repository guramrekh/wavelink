from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import BooleanField, SelectField, StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, ValidationError

from myapp.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=32)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=32)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=32)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class AccountUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=32)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=300)])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    restore_default_picture = BooleanField('Restore default profile picture', default=False)
            
    update = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')


class PlaylistCreationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=32)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    cover_photo = FileField('Cover', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'])])
    visibility = SelectField('Visibility', choices=[('public', 'Public'), ('private', 'Private')],
                                        default='private', validators=[DataRequired()])
    create = SubmitField('Create')


class PlaylistUpdateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=32)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    cover_photo = FileField('Cover', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'])])
    visibility = SelectField('Visibility', choices=[('public', 'Public'), ('private', 'Private')],
                                        default='private', validators=[DataRequired()])
    restore_default_cover = BooleanField('Restore default cover', default=False)
    edit = SubmitField('Edit')