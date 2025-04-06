from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return render_template("home.html")

@bp.route('/login')
def login():
    return render_template("login.html")

@bp.route('/register')
def register():
    return render_template("register.html")