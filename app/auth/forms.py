from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.auth.models import User

# the form = registratoinForm, field is the name of the field on which
#we are going to apply custom validation, in our case it is email.
#user_email = the exact name of the attributes in the users database table..
# field.data will have access to email field of the web control
def email_exists(form, field):
    email = User.query.filter_by(user_email=field.data).first()
    if email:
        raise ValidationError('Email Already Exists')

class RegistrationForm(FlaskForm):

    name = StringField('Name', validators=[DataRequired(), Length(3, 15, message='between 3 to 15 characters')])
    email = StringField('E-mail', validators=[DataRequired(), Email(), email_exists])
    password = PasswordField('Password', validators=[DataRequired(), Length(5), EqualTo('confirm', message='password must match')])
    confirm = PasswordField('Confirm', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    stay_loggedin = BooleanField('stay logged-in')
    submit = SubmitField('LogIn')
