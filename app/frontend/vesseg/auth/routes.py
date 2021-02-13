from flask import redirect, url_for, flash, render_template
from flask_login import logout_user, login_user, current_user
from .forms import LoginForm, SignupForm
from . import bp
from ..models import User
from .. import db


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
            redirect(url_for('main.project'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('auth.login'))
        user.update_last_login()
        login_user(user)
        return redirect(url_for('main.home'))
    return render_template('auth/login.html', form=form)


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.project'))
    form = SignupForm()
    if form.validate_on_submit():
        admin = True if len(User.query.all())==0 else False
        user = User(username=form.username.data, email=form.email.data, admin=admin)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/signup.html', form=form)


@bp.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('auth.login'))