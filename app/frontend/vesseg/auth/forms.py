from flask_wtf import FlaskForm
from flask import current_app
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from ..models import User


class SignupForm(FlaskForm):

    username = StringField('username', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired(), Email(message='Enter a valid email.')])
    # signuptoken = StringField('sign up token', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=8, message='Password must be at least 8 characters long.')])
    confirm = PasswordField('confirm your password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    # def validate_signuptoken(self, signuptoken):
    #     if current_app.config['SIGNUP_TOKEN'] != signuptoken.data:
    #         raise ValidationError('Please enter a valid sign-up token.')



class LoginForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('login')

