from flask import Blueprint, render_template, flash, redirect, url_for
from .forms import RegistrationForm, LoginForm

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
    return render_template('login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
    else:
        return render_template('register.html', form=form)