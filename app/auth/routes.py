from app.auth import authentication as at
from flask import session as login_session
from app.auth.forms import RegistrationForm, LoginForm
from flask_login import login_user, logout_user, login_required, current_user
from flask import render_template, request, redirect, url_for, flash # for flash messaging

# you can use create_user method to create user in the database
from app.auth.models import User

@at.route('/register', methods = ['GET', 'POST'])
@login_required
def register_user():

    if current_user.is_authenticated:
        flash('you are already logged-in')
        return redirect(url_for('main.home'))

    form = RegistrationForm()

    if form.validate_on_submit():
        User.create_user(
         user = form.name.data,
         email = form.email.data,
         password = form.password.data
        )

        flash('Registration Successfull')

        return redirect(url_for('authentication.do_the_login'))

    return render_template('registration.html', form=form)


@at.route('/login', methods=['GET', 'POST'])
def do_the_login():
    if current_user.is_authenticated:
        flash('you are already logged-in')
        return redirect(url_for('main.home'))
    form = LoginForm()
    # if its a POST request
    if form.validate_on_submit():
        user = User.query.filter_by(user_email=form.email.data).first()
        if not user or not user.check_password(form.password.data):
            flash('Invalid Credentials, Please try again')
            return redirect(url_for('authentication.do_the_login'))
        # login_user is the buil-in method, we have already imported before
        login_user(user, form.stay_loggedin.data)
        login_session['id'] = user.id
        return redirect(url_for('main.home'))
    return render_template('login.html', form=form)


@at.route('/logout')
@login_required
def log_out_user():
    # log_out_user is buil-in method!!!
    logout_user()
    flash('Logged out Successfully')
    return redirect(url_for('main.home'))

@at.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
