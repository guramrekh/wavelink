import os

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'myapp.sqlite')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import routes 
    app.register_blueprint(routes.bp)  

    from myapp.extensions import db, bcrypt, login_manager
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'main.login' 
    login_manager.login_message_category = 'info'


    app.jinja_env.filters['format_duration'] = format_duration


    return app



def format_duration(seconds):
    if seconds is None:
        return '--:--'
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"