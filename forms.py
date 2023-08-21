from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Register')


class EditForm(FlaskForm):
    rating = StringField('Rating')
    review = StringField('Review')
    submit = SubmitField('Change')


class AddForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('submit')